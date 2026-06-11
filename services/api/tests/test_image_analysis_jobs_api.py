import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


class ImageAnalysisJobsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_create_upload_ticket_then_analysis_job_and_fetch_status(self):
        upload_response = self.client.post(
            "/api/v1/closet-items/uploads",
            json={
                "fileName": "white shirt.jpg",
                "contentType": "image/jpeg",
                "byteSize": 12345,
                "checksumSha256": "abc123",
            },
        )

        self.assertEqual(upload_response.status_code, 201)
        upload = upload_response.json()
        self.assertIn("uploadId", upload)
        self.assertEqual(upload["method"], "PUT")
        self.assertEqual(upload["headers"]["Content-Type"], "image/jpeg")
        self.assertTrue(upload["storageKey"].endswith("/white-shirt.jpg"))
        self.assertEqual(upload["uploadUrl"], f"/api/v1/closet-items/uploads/{upload['uploadId']}/object")

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

    def test_job_status_returns_404_for_missing_job(self):
        response = self.client.get("/api/v1/closet-items/jobs/missing-job")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
