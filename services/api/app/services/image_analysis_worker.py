from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain import ImageAnalysisJob, ImageAnalysisJobStatus
from .image_analysis_provider import ImageAnalysisProvider


class ImageAnalysisJobRepository(Protocol):
    def list_jobs_by_status(self, status: ImageAnalysisJobStatus, limit: int = 10) -> list[ImageAnalysisJob]:
        ...

    def update_job(
        self,
        job_id: str,
        *,
        status: ImageAnalysisJobStatus | None = None,
        progress: int | None = None,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> ImageAnalysisJob:
        ...


class UploadObjectStorage(Protocol):
    def read(self, storage_key: str) -> bytes:
        ...


@dataclass(frozen=True)
class ImageAnalysisWorkerResult:
    processed: bool
    reason: str
    job: ImageAnalysisJob | None = None


def process_next_image_analysis_job(
    repository: ImageAnalysisJobRepository,
    upload_storage: UploadObjectStorage,
    provider: ImageAnalysisProvider,
) -> ImageAnalysisWorkerResult:
    queued_jobs = repository.list_jobs_by_status(ImageAnalysisJobStatus.QUEUED, limit=1)
    if not queued_jobs:
        return ImageAnalysisWorkerResult(processed=False, reason="no_queued_jobs")

    queued_job = queued_jobs[0]
    running_job = repository.update_job(
        queued_job.id,
        status=ImageAnalysisJobStatus.RUNNING,
        progress=35,
        error=None,
    )

    try:
        image_bytes = upload_storage.read(running_job.storage_key)
        result = provider.analyze(running_job, image_bytes)
        quality = result["quality"]
        completion_status = (
            ImageAnalysisJobStatus.SUCCEEDED
            if isinstance(quality, dict) and quality.get("usable") is True
            else ImageAnalysisJobStatus.NEEDS_USER_REVIEW
        )
        completed_job = repository.update_job(
            running_job.id,
            status=completion_status,
            progress=100,
            result=result,
            error=None,
        )
    except Exception as error:
        failed_job = repository.update_job(
            running_job.id,
            status=ImageAnalysisJobStatus.FAILED,
            progress=100,
            error=str(error),
        )
        return ImageAnalysisWorkerResult(processed=True, reason="failed", job=failed_job)

    return ImageAnalysisWorkerResult(processed=True, reason="processed", job=completed_job)
