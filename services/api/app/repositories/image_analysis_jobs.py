from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from ..db.models import ImageAnalysisJobRecord, ImageUploadTicketRecord, WorkerEventRecord
from ..db.session import session_scope
from ..domain import ImageAnalysisJob, ImageAnalysisJobStatus, ImageUploadTicket, WorkerEvent


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


class SqlAlchemyImageAnalysisRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

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

        with session_scope(self._session_factory) as session:
            session.add(_upload_ticket_to_record(ticket))

        return ticket

    def get_upload_ticket(self, upload_id: str) -> ImageUploadTicket:
        with session_scope(self._session_factory) as session:
            record = session.get(ImageUploadTicketRecord, upload_id)
            if record is None:
                raise ImageUploadNotFoundError(upload_id)
            return _upload_ticket_record_to_domain(record)

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

        with session_scope(self._session_factory) as session:
            session.add(_analysis_job_to_record(job))
            session.add(_worker_event_to_record(event))

        return job, event

    def get_job(self, job_id: str) -> ImageAnalysisJob:
        with session_scope(self._session_factory) as session:
            record = session.get(ImageAnalysisJobRecord, job_id)
            if record is None:
                raise ImageAnalysisJobNotFoundError(job_id)
            return _analysis_job_record_to_domain(record)

    def get_worker_event(self, job_id: str) -> WorkerEvent:
        with session_scope(self._session_factory) as session:
            record = session.get(WorkerEventRecord, job_id)
            if record is None:
                raise ImageAnalysisJobNotFoundError(job_id)
            return _worker_event_record_to_domain(record)


def _upload_ticket_to_record(ticket: ImageUploadTicket) -> ImageUploadTicketRecord:
    return ImageUploadTicketRecord(
        id=ticket.id,
        upload_url=ticket.upload_url,
        storage_key=ticket.storage_key,
        file_name=ticket.file_name,
        content_type=ticket.content_type,
        byte_size=ticket.byte_size,
        checksum_sha256=ticket.checksum_sha256,
        expires_at=ticket.expires_at,
        method=ticket.method,
        headers=ticket.headers,
    )


def _upload_ticket_record_to_domain(record: ImageUploadTicketRecord) -> ImageUploadTicket:
    return ImageUploadTicket(
        id=record.id,
        upload_url=record.upload_url,
        storage_key=record.storage_key,
        file_name=record.file_name,
        content_type=record.content_type,
        byte_size=record.byte_size,
        checksum_sha256=record.checksum_sha256,
        expires_at=record.expires_at,
        method=record.method,
        headers=dict(record.headers),
    )


def _analysis_job_to_record(job: ImageAnalysisJob) -> ImageAnalysisJobRecord:
    return ImageAnalysisJobRecord(
        id=job.id,
        upload_id=job.upload_id,
        storage_key=job.storage_key,
        original_file_name=job.original_file_name,
        content_type=job.content_type,
        requested_operations=list(job.requested_operations),
        status=job.status.value,
        progress=job.progress,
        result=job.result,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _analysis_job_record_to_domain(record: ImageAnalysisJobRecord) -> ImageAnalysisJob:
    return ImageAnalysisJob(
        id=record.id,
        upload_id=record.upload_id,
        storage_key=record.storage_key,
        original_file_name=record.original_file_name,
        content_type=record.content_type,
        requested_operations=tuple(record.requested_operations),
        status=ImageAnalysisJobStatus(record.status),
        progress=record.progress,
        result=record.result,
        error=record.error,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _worker_event_to_record(event: WorkerEvent) -> WorkerEventRecord:
    return WorkerEventRecord(
        job_id=event.job_id,
        event_type=event.event_type,
        upload_id=event.upload_id,
        storage_key=event.storage_key,
        requested_operations=list(event.requested_operations),
    )


def _worker_event_record_to_domain(record: WorkerEventRecord) -> WorkerEvent:
    return WorkerEvent(
        event_type=record.event_type,
        job_id=record.job_id,
        upload_id=record.upload_id,
        storage_key=record.storage_key,
        requested_operations=tuple(record.requested_operations),
    )
