import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


def storage_settings(root: Path) -> Settings:
    return Settings(
        environment="test",
        upload_storage_root=str(root),
    )


class UploadStorageApiTests(unittest.TestCase):
    def test_upload_ticket_accepts_raw_object_and_stores_file(self):
        with tempfile.TemporaryDirectory() as directory:
            storage_root = Path(directory) / "uploads"
            client = TestClient(create_app(storage_settings(storage_root)))
            payload = b"fake jpeg bytes"
            checksum = hashlib.sha256(payload).hexdigest()

            upload_response = client.post(
                "/api/v1/closet-items/uploads",
                json={
                    "fileName": "white shirt.jpg",
                    "contentType": "image/jpeg",
                    "byteSize": len(payload),
                    "checksumSha256": checksum,
                },
            )
            self.assertEqual(upload_response.status_code, 201)
            upload = upload_response.json()
            self.assertEqual(upload["uploadUrl"], f"/api/v1/closet-items/uploads/{upload['uploadId']}/object")

            completion_response = client.put(
                upload["uploadUrl"],
                content=payload,
                headers={"Content-Type": "image/jpeg"},
            )

            self.assertEqual(completion_response.status_code, 200)
            completion = completion_response.json()
            self.assertTrue(completion["uploaded"])
            self.assertEqual(completion["uploadId"], upload["uploadId"])
            self.assertEqual(completion["storageKey"], upload["storageKey"])
            self.assertEqual(completion["contentType"], "image/jpeg")
            self.assertEqual(completion["byteSize"], len(payload))
            self.assertEqual(completion["checksumSha256"], checksum)
            self.assertEqual((storage_root / upload["storageKey"]).read_bytes(), payload)

            job_response = client.post(
                "/api/v1/closet-items/analyze",
                json={"uploadId": upload["uploadId"]},
            )
            self.assertEqual(job_response.status_code, 202)
            self.assertEqual(job_response.json()["status"], "queued")

    def test_upload_object_rejects_invalid_completion_payloads(self):
        with tempfile.TemporaryDirectory() as directory:
            storage_root = Path(directory) / "uploads"
            client = TestClient(create_app(storage_settings(storage_root)))
            upload_response = client.post(
                "/api/v1/closet-items/uploads",
                json={
                    "fileName": "black-loafers.jpg",
                    "contentType": "image/jpeg",
                    "byteSize": 4,
                    "checksumSha256": hashlib.sha256(b"good").hexdigest(),
                },
            )
            self.assertEqual(upload_response.status_code, 201)
            upload = upload_response.json()

            content_type_response = client.put(
                upload["uploadUrl"],
                content=b"good",
                headers={"Content-Type": "image/png"},
            )
            self.assertEqual(content_type_response.status_code, 415)

            byte_size_response = client.put(
                upload["uploadUrl"],
                content=b"too-long",
                headers={"Content-Type": "image/jpeg"},
            )
            self.assertEqual(byte_size_response.status_code, 400)

            checksum_response = client.put(
                upload["uploadUrl"],
                content=b"nope",
                headers={"Content-Type": "image/jpeg"},
            )
            self.assertEqual(checksum_response.status_code, 400)
            self.assertFalse((storage_root / upload["storageKey"]).exists())

    def test_upload_object_returns_404_for_missing_ticket(self):
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(storage_settings(Path(directory) / "uploads")))

            response = client.put(
                "/api/v1/closet-items/uploads/missing-upload/object",
                content=b"body",
                headers={"Content-Type": "image/jpeg"},
            )

            self.assertEqual(response.status_code, 404)

    def test_analysis_rejects_completed_ticket_when_stored_object_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            storage_root = Path(directory) / "uploads"
            client = TestClient(create_app(storage_settings(storage_root)))
            payload = b"temporary image bytes"
            upload_response = client.post(
                "/api/v1/closet-items/uploads",
                json={"fileName": "missing.jpg", "contentType": "image/jpeg", "byteSize": len(payload)},
            )
            self.assertEqual(upload_response.status_code, 201)
            upload = upload_response.json()

            completion_response = client.put(
                upload["uploadUrl"],
                content=payload,
                headers={"Content-Type": "image/jpeg"},
            )
            self.assertEqual(completion_response.status_code, 200)
            (storage_root / upload["storageKey"]).unlink()

            response = client.post(
                "/api/v1/closet-items/analyze",
                json={"uploadId": upload["uploadId"]},
            )

            self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
