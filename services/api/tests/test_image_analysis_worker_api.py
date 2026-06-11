import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


def sqlite_settings(path: Path) -> Settings:
    return Settings(
        environment="test",
        repository_backend="sqlite",
        database_url=f"sqlite:///{path}",
    )


def create_analysis_job(client: TestClient, file_name: str = "white shirt.jpg") -> dict[str, object]:
    upload_response = client.post(
        "/api/v1/closet-items/uploads",
        json={"fileName": file_name, "contentType": "image/jpeg"},
    )
    assert upload_response.status_code == 201

    job_response = client.post(
        "/api/v1/closet-items/analyze",
        json={"uploadId": upload_response.json()["uploadId"]},
    )
    assert job_response.status_code == 202
    return job_response.json()


class ImageAnalysisWorkerApiTests(unittest.TestCase):
    def test_process_next_job_creates_placeholder_analysis_result(self):
        client = TestClient(create_app())
        job = create_analysis_job(client)

        process_response = client.post("/api/v1/closet-items/jobs/process-next")

        self.assertEqual(process_response.status_code, 200)
        body = process_response.json()
        self.assertTrue(body["processed"])
        self.assertEqual(body["reason"], "processed")
        self.assertEqual(body["jobId"], job["jobId"])
        self.assertEqual(body["status"], "succeeded")
        self.assertEqual(body["progress"], 100)

        result = body["result"]
        self.assertEqual(result["provider"], "fitlog_stub")
        self.assertEqual(result["modelVersion"], "image-analysis-worker-stub-v1")
        self.assertEqual(result["quality"]["usable"], True)
        self.assertEqual(result["detectedAttributes"]["category"], "top")
        self.assertEqual(result["detectedAttributes"]["subType"], "shirt")
        self.assertEqual(result["closetItemDraft"]["category"], "top")
        self.assertEqual(result["closetItemDraft"]["colors"][0], "white")
        self.assertEqual(result["illustration"]["status"], "placeholder")
        self.assertEqual(result["illustration"]["storageKey"], f"illustrations/{job['jobId']}.png")

        status_response = client.get(f"/api/v1/closet-items/jobs/{job['jobId']}")
        self.assertEqual(status_response.status_code, 200)
        status_body = status_response.json()
        self.assertEqual(status_body["status"], "succeeded")
        self.assertEqual(status_body["progress"], 100)
        self.assertEqual(status_body["result"]["closetItemDraft"]["subType"], "shirt")

    def test_process_next_returns_idle_response_when_no_jobs_are_queued(self):
        client = TestClient(create_app())

        response = client.post("/api/v1/closet-items/jobs/process-next")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["processed"])
        self.assertEqual(body["reason"], "no_queued_jobs")
        self.assertIsNone(body["jobId"])
        self.assertIsNone(body["status"])
        self.assertIsNone(body["result"])

    def test_sqlite_worker_result_persists_across_app_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "fitlog-test.db"

            first_client = TestClient(create_app(sqlite_settings(database_path)))
            job = create_analysis_job(first_client, file_name="black-loafers.jpg")

            process_response = first_client.post("/api/v1/closet-items/jobs/process-next")
            self.assertEqual(process_response.status_code, 200)
            self.assertEqual(process_response.json()["status"], "succeeded")

            second_client = TestClient(create_app(sqlite_settings(database_path)))
            status_response = second_client.get(f"/api/v1/closet-items/jobs/{job['jobId']}")

            self.assertEqual(status_response.status_code, 200)
            body = status_response.json()
            self.assertEqual(body["status"], "succeeded")
            self.assertEqual(body["progress"], 100)
            self.assertEqual(body["result"]["closetItemDraft"]["category"], "shoes")
            self.assertEqual(body["result"]["closetItemDraft"]["subType"], "loafers")
            self.assertEqual(body["result"]["closetItemDraft"]["colors"][0], "black")


if __name__ == "__main__":
    unittest.main()
