from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from ..domain import ImageAnalysisJob, ImageUploadTicket, WorkerEvent


class ImageUploadNotFoundError(Exception):
    pass


class ImageAnalysisJobNotFoundError(Exception):
    pass


class InMemoryImageAnalysisRepository:
    def __init__(self):
        self._uploads: dict[str, ImageUploadTicket] = {}
        self._jobs: dict[str, ImageAnalysisJob] = {}
        self._events: dict[str, WorkerEvent] = {}

    def create_upload_ticket(
        self,
        file_name: str,
        content_type: str,
        byte_size: int | None = None,
        checksum_sha256: str | None = None,
    ) -> ImageUploadTicket:
        upload_id = uuid4().hex
        safe_name = _safe_file_name(file_name)
        storage_key = f"uploads/{upload_id}/{safe_name}"
        ticket = ImageUploadTicket(
            id=upload_id,
            upload_url=f"memory://fitlog/{storage_key}",
            storage_key=storage_key,
            file_name=file_name,
            content_type=content_type,
            byte_size=byte_size,
            checksum_sha256=checksum_sha256,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            headers={"Content-Type": content_type},
        )
        self._uploads[upload_id] = ticket
        return ticket

    def get_upload_ticket(self, upload_id: str) -> ImageUploadTicket:
        try:
            return self._uploads[upload_id]
        except KeyError as error:
            raise ImageUploadNotFoundError(upload_id) from error

    def create_analysis_job(
        self,
        upload_id: str,
        requested_operations: tuple[str, ...],
    ) -> tuple[ImageAnalysisJob, WorkerEvent]:
        upload = self.get_upload_ticket(upload_id)
        now = datetime.now(timezone.utc)
        job_id = uuid4().hex
        job = ImageAnalysisJob(
            id=job_id,
            upload_id=upload.id,
            storage_key=upload.storage_key,
            original_file_name=upload.file_name,
            content_type=upload.content_type,
            requested_operations=requested_operations,
            created_at=now,
            updated_at=now,
        )
        event = WorkerEvent(
            event_type="image.uploaded",
            job_id=job.id,
            upload_id=upload.id,
            storage_key=upload.storage_key,
            requested_operations=requested_operations,
        )
        self._jobs[job.id] = job
        self._events[job.id] = event
        return job, event

    def get_job(self, job_id: str) -> ImageAnalysisJob:
        try:
            return self._jobs[job_id]
        except KeyError as error:
            raise ImageAnalysisJobNotFoundError(job_id) from error

    def get_worker_event(self, job_id: str) -> WorkerEvent:
        self.get_job(job_id)
        return self._events[job_id]


def _safe_file_name(file_name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", file_name).strip("-")
    return normalized or "upload"

