import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.domain import ImageAnalysisJob  # noqa: E402
from app.main import create_app  # noqa: E402
from app.repositories.image_analysis_jobs import InMemoryImageAnalysisRepository  # noqa: E402
from app.services.image_analysis_provider import (  # noqa: E402
    DeterministicImageAnalysisProvider,
    ImageAnalysisProviderError,
    OpenAIImageAnalysisProvider,
    OpenAIProviderConfigurationError,
    OpenAIResponsesError,
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


class FailingProvider:
    name = "failing"

    def analyze(self, job, image_bytes: bytes) -> dict[str, object]:
        raise ImageAnalysisProviderError("provider unavailable")


class StubResponsesClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create_response(self, payload: dict[str, object], timeout_seconds: float) -> dict[str, object]:
        self.calls.append((payload, timeout_seconds))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def analysis_job(content_type: str = "image/jpeg") -> ImageAnalysisJob:
    return ImageAnalysisJob(
        id="job-123",
        upload_id="upload-123",
        storage_key="uploads/upload-123/shirt.jpg",
        original_file_name="shirt.jpg",
        content_type=content_type,
        requested_operations=("quality_check", "attribute_extraction", "illustration"),
    )


def successful_openai_response() -> dict[str, object]:
    output = {
        "quality": {"usable": True, "score": 0.94, "issues": []},
        "detectedAttributes": {
            "category": "top",
            "subType": "shirt",
            "colors": [{"name": "white", "hex": "#FFFFFF", "role": "primary"}],
            "pattern": "solid",
            "materialGuess": ["cotton"],
            "thickness": "medium",
            "seasons": ["all"],
            "fit": "regular",
            "formality": "business_casual",
            "styleTags": ["minimal", "workwear"],
        },
        "closetItemDraft": {
            "name": "White shirt",
            "category": "top",
            "subType": "shirt",
            "seasons": ["all"],
            "styleTags": ["minimal", "workwear"],
            "colors": ["white"],
            "thickness": "medium",
            "formality": "business_casual",
            "status": "available",
            "warmth": 4,
            "rainSafe": False,
            "breathability": 7,
        },
        "confidence": {"category": 0.96, "colors": 0.91, "styleTags": 0.82},
    }
    return {
        "id": "resp-123",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(output)}],
            }
        ],
    }


class ImageAnalysisProviderTests(unittest.TestCase):
    def test_factory_builds_deterministic_provider(self):
        provider = build_image_analysis_provider(" Deterministic ")

        self.assertIsInstance(provider, DeterministicImageAnalysisProvider)

    def test_factory_builds_demo_provider(self):
        provider = build_image_analysis_provider("demo")

        self.assertIsInstance(provider, DeterministicImageAnalysisProvider)

    def test_app_rejects_unknown_provider_configuration(self):
        with self.assertRaisesRegex(ValueError, "Unsupported image analysis provider"):
            create_app(Settings(image_analysis_provider="unknown"))

    def test_openai_provider_requires_api_key(self):
        with self.assertRaises(OpenAIProviderConfigurationError):
            build_image_analysis_provider("openai")

    def test_openai_provider_sends_image_and_normalizes_structured_output(self):
        client = StubResponsesClient([successful_openai_response()])
        provider = OpenAIImageAnalysisProvider(
            api_key="test-key",
            model="gpt-5.4-mini",
            base_url="https://api.openai.com/v1",
            timeout_seconds=12.5,
            max_retries=0,
            client=client,
        )
        image_bytes = b"real jpeg bytes"

        result = provider.analyze(analysis_job(), image_bytes)

        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["modelVersion"], "gpt-5.4-mini")
        self.assertEqual(result["detectedAttributes"]["category"], "top")
        self.assertEqual(result["closetItemDraft"]["colors"], ["white"])
        self.assertEqual(result["illustration"]["status"], "placeholder")
        self.assertEqual(result["confidence"]["illustration"], 0.0)

        payload, timeout_seconds = client.calls[0]
        self.assertEqual(timeout_seconds, 12.5)
        self.assertEqual(payload["model"], "gpt-5.4-mini")
        self.assertFalse(payload["store"])
        self.assertTrue(payload["text"]["format"]["strict"])
        image_input = payload["input"][0]["content"][1]
        self.assertEqual(image_input["type"], "input_image")
        self.assertEqual(image_input["detail"], "high")
        self.assertEqual(
            image_input["image_url"],
            f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('ascii')}",
        )

    def test_openai_provider_retries_transient_responses_api_error(self):
        client = StubResponsesClient(
            [OpenAIResponsesError("rate limited", status_code=429), successful_openai_response()]
        )
        sleep_delays = []
        provider = OpenAIImageAnalysisProvider(
            api_key="test-key",
            model="gpt-5.4-mini",
            base_url="https://api.openai.com/v1",
            timeout_seconds=30,
            max_retries=2,
            client=client,
            sleep=sleep_delays.append,
        )

        result = provider.analyze(analysis_job(), b"jpeg")

        self.assertEqual(result["provider"], "openai")
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(sleep_delays, [0.25])

    def test_openai_provider_rejects_invalid_structured_output(self):
        response = {
            "output": [{"type": "message", "content": [{"type": "output_text", "text": "{}"}]}]
        }
        provider = OpenAIImageAnalysisProvider(
            api_key="test-key",
            model="gpt-5.4-mini",
            base_url="https://api.openai.com/v1",
            timeout_seconds=30,
            max_retries=0,
            client=StubResponsesClient([response]),
        )

        with self.assertRaises(ImageAnalysisProviderError):
            provider.analyze(analysis_job(), b"jpeg")

    def test_openai_provider_rejects_unsupported_image_content_type(self):
        provider = OpenAIImageAnalysisProvider(
            api_key="test-key",
            model="gpt-5.4-mini",
            base_url="https://api.openai.com/v1",
            timeout_seconds=30,
            max_retries=0,
            client=StubResponsesClient([]),
        )

        with self.assertRaisesRegex(ImageAnalysisProviderError, "Unsupported image content type"):
            provider.analyze(analysis_job("image/heic"), b"heic")

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

    def test_worker_persists_provider_failure_on_analysis_job(self):
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

            result = process_next_image_analysis_job(repository, storage, FailingProvider())

            self.assertTrue(result.processed)
            self.assertEqual(result.reason, "failed")
            self.assertEqual(result.job.id, job.id)
            self.assertEqual(result.job.status.value, "failed")
            self.assertEqual(result.job.progress, 100)
            self.assertEqual(result.job.error, "provider unavailable")


if __name__ == "__main__":
    unittest.main()
