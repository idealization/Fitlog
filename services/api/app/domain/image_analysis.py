from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .enums import ImageAnalysisJobStatus


@dataclass(frozen=True)
class ImageUploadTicket:
    id: str
    upload_url: str
    storage_key: str
    file_name: str
    content_type: str
    byte_size: int | None
    checksum_sha256: str | None
    expires_at: datetime
    method: str = "PUT"
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkerEvent:
    event_type: str
    job_id: str
    upload_id: str
    storage_key: str
    requested_operations: tuple[str, ...]


@dataclass(frozen=True)
class ImageAnalysisJob:
    id: str
    upload_id: str
    storage_key: str
    original_file_name: str
    content_type: str
    requested_operations: tuple[str, ...]
    status: ImageAnalysisJobStatus = ImageAnalysisJobStatus.QUEUED
    progress: int = 0
    result: dict[str, object] | None = None
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

