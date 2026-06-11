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
        upload_storage_root=str(path.parent / "uploads"),
    )


def closet_item_payload(item_id="persisted-shirt"):
    return {
        "id": item_id,
        "name": "Persisted white shirt",
        "category": "top",
        "subType": "shirt",
        "seasons": ["all"],
        "styleTags": ["minimal"],
        "colors": ["white"],
        "formality": "business_casual",
        "warmth": 4,
        "breathability": 7,
    }


class PersistenceFoundationTests(unittest.TestCase):
    def test_sqlite_closet_items_persist_across_app_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "fitlog-test.db"

            first_client = TestClient(create_app(sqlite_settings(database_path)))
            create_response = first_client.post("/api/v1/closet-items", json=closet_item_payload())
            self.assertEqual(create_response.status_code, 201)

            second_client = TestClient(create_app(sqlite_settings(database_path)))
            list_response = second_client.get("/api/v1/closet-items")

            self.assertEqual(list_response.status_code, 200)
            items = list_response.json()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["id"], "persisted-shirt")

    def test_sqlite_image_analysis_jobs_persist_across_app_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "fitlog-test.db"

            first_client = TestClient(create_app(sqlite_settings(database_path)))
            upload_response = first_client.post(
                "/api/v1/closet-items/uploads",
                json={"fileName": "shirt.jpg", "contentType": "image/jpeg"},
            )
            self.assertEqual(upload_response.status_code, 201)
            upload = upload_response.json()
            upload_id = upload["uploadId"]

            premature_job_response = first_client.post(
                "/api/v1/closet-items/analyze",
                json={"uploadId": upload_id},
            )
            self.assertEqual(premature_job_response.status_code, 409)

            completion_response = first_client.put(
                upload["uploadUrl"],
                content=b"persisted image bytes",
                headers={"Content-Type": "image/jpeg"},
            )
            self.assertEqual(completion_response.status_code, 200)

            second_client = TestClient(create_app(sqlite_settings(database_path)))
            job_response = second_client.post(
                "/api/v1/closet-items/analyze",
                json={"uploadId": upload_id},
            )
            self.assertEqual(job_response.status_code, 202)
            job_id = job_response.json()["jobId"]

            third_client = TestClient(create_app(sqlite_settings(database_path)))
            status_response = third_client.get(f"/api/v1/closet-items/jobs/{job_id}")

            self.assertEqual(status_response.status_code, 200)
            body = status_response.json()
            self.assertEqual(body["jobId"], job_id)
            self.assertEqual(body["uploadId"], upload_id)
            self.assertEqual(body["status"], "queued")


if __name__ == "__main__":
    unittest.main()
