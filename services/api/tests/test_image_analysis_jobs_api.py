import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


class ImageAnalysisJobsApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        settings = Settings(
            environment="test",
            upload_storage_root=str(Path(self.temp_directory.name) / "uploads"),
        )
        self.client = TestClient(create_app(settings))

    def test_create_upload_ticket_then_analysis_job_and_fetch_status(self):
        payload = b"fake white shirt jpeg"
        upload_response = self.client.post(
            "/api/v1/closet-items/uploads",
            json={
                "fileName": "white shirt.jpg",
                "contentType": "image/jpeg",
                "byteSize": len(payload),
                "checksumSha256": hashlib.sha256(payload).hexdigest(),
            },
        )

        self.assertEqual(upload_response.status_code, 201)
        upload = upload_response.json()
        self.assertIn("uploadId", upload)
        self.assertEqual(upload["method"], "PUT")
        self.assertEqual(upload["headers"]["Content-Type"], "image/jpeg")
        self.assertTrue(upload["storageKey"].endswith("/white-shirt.jpg"))
        self.assertEqual(upload["uploadUrl"], f"/api/v1/closet-items/uploads/{upload['uploadId']}/object")

        completion_response = self.client.put(
            upload["uploadUrl"],
            content=payload,
            headers={"Content-Type": "image/jpeg"},
        )
        self.assertEqual(completion_response.status_code, 200)

        job_response = self.client.post(
            "/api/v1/closet-items/analyze",
            json={
                "uploadId": upload["uploadId"],
                "requestedOperations": ["quality_check", "attribute_extraction", "illustration"],
            },
        )

        self.assertEqual(job_response.status_code, 202)
        job = job_response.json()
        self.assertEqual(job["status"], "queued")
        self.assertEqual(job["progress"], 0)
        self.assertEqual(job["uploadId"], upload["uploadId"])
        self.assertEqual(job["workerEvent"]["eventType"], "image.uploaded")
        self.assertEqual(job["workerEvent"]["storageKey"], upload["storageKey"])
        self.assertEqual(job["workerEvent"]["requestedOperations"][0], "quality_check")

        status_response = self.client.get(f"/api/v1/closet-items/jobs/{job['jobId']}")

        self.assertEqual(status_response.status_code, 200)
        status_body = status_response.json()
        self.assertEqual(status_body["jobId"], job["jobId"])
        self.assertEqual(status_body["type"], "closet_item_analysis")
        self.assertIsNone(status_body["workerEvent"])

    def test_analysis_job_creation_returns_404_for_missing_upload(self):
        response = self.client.post(
            "/api/v1/closet-items/analyze",
            json={"uploadId": "missing-upload"},
        )

        self.assertEqual(response.status_code, 404)

    def test_analysis_job_creation_returns_409_until_upload_is_completed(self):
        upload_response = self.client.post(
            "/api/v1/closet-items/uploads",
            json={"fileName": "pending.jpg", "contentType": "image/jpeg"},
        )
        self.assertEqual(upload_response.status_code, 201)

        response = self.client.post(
            "/api/v1/closet-items/analyze",
            json={"uploadId": upload_response.json()["uploadId"]},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], "Upload object is not ready for analysis.")

    def test_job_status_returns_404_for_missing_job(self):
        response = self.client.get("/api/v1/closet-items/jobs/missing-job")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
