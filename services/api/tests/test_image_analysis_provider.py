import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.repositories.image_analysis_jobs import InMemoryImageAnalysisRepository  # noqa: E402
from app.services.image_analysis_provider import (  # noqa: E402
    DeterministicImageAnalysisProvider,
    build_image_analysis_provider,
)
from app.services.image_analysis_worker import process_next_image_analysis_job  # noqa: E402
from app.services.upload_storage import LocalUploadStorage  # noqa: E402


class RecordingProvider:
    name = "recording"

    def __init__(self):
        self.image_bytes = b""

    def analyze(self, job, image_bytes: bytes) -> dict[str, object]:
        self.image_bytes = image_bytes
        return {
            "provider": self.name,
            "source": {"jobId": job.id},
            "quality": {"usable": True, "score": 1.0, "issues": []},
        }


class ImageAnalysisProviderTests(unittest.TestCase):
    def test_factory_builds_deterministic_provider(self):
        provider = build_image_analysis_provider(" Deterministic ")

        self.assertIsInstance(provider, DeterministicImageAnalysisProvider)

    def test_app_rejects_unknown_provider_configuration(self):
        with self.assertRaisesRegex(ValueError, "Unsupported image analysis provider"):
            create_app(Settings(image_analysis_provider="unknown"))

    def test_worker_reads_stored_image_bytes_and_injects_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = InMemoryImageAnalysisRepository()
            storage = LocalUploadStorage(Path(directory))
            payload = b"provider input image bytes"
            upload = repository.create_upload_ticket("shirt.jpg", "image/jpeg", byte_size=len(payload))
            stored_object = storage.save(upload.storage_key, upload.content_type, payload)
            repository.mark_upload_completed(
                upload.id,
                byte_size=stored_object.byte_size,
                checksum_sha256=stored_object.checksum_sha256,
            )
            job, _ = repository.create_analysis_job(upload.id, ("quality_check",))
            provider = RecordingProvider()

            result = process_next_image_analysis_job(repository, storage, provider)

            self.assertTrue(result.processed)
            self.assertEqual(result.reason, "processed")
            self.assertEqual(result.job.id, job.id)
            self.assertEqual(result.job.result["provider"], "recording")
            self.assertEqual(provider.image_bytes, payload)


if __name__ == "__main__":
    unittest.main()
