from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field

from ....domain import ImageAnalysisJob, ImageAnalysisJobStatus, ImageUploadTicket, WorkerEvent
from ....services.image_analysis_worker import ImageAnalysisWorkerResult
from ....services.upload_storage import StoredUploadObject

DEFAULT_REQUESTED_OPERATIONS = ["quality_check", "attribute_extraction", "illustration"]


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, use_enum_values=False)


class UploadUrlRequest(ApiModel):
    file_name: str = Field(alias="fileName")
    content_type: str = Field(alias="contentType")
    byte_size: Annotated[Optional[int], Field(ge=1)] = Field(default=None, alias="byteSize")
    checksum_sha256: Optional[str] = Field(default=None, alias="checksumSha256")


class UploadUrlResponse(ApiModel):
    upload_id: str = Field(alias="uploadId")
    upload_url: str = Field(alias="uploadUrl")
    method: str
    storage_key: str = Field(alias="storageKey")
    expires_at: datetime = Field(alias="expiresAt")
    headers: dict[str, str]


class UploadCompletionResponse(ApiModel):
    upload_id: str = Field(alias="uploadId")
    uploaded: bool
    storage_key: str = Field(alias="storageKey")
    content_type: str = Field(alias="contentType")
    byte_size: int = Field(alias="byteSize")
    checksum_sha256: str = Field(alias="checksumSha256")


class AnalysisJobCreateRequest(ApiModel):
    upload_id: str = Field(alias="uploadId")
    requested_operations: list[str] = Field(default_factory=lambda: list(DEFAULT_REQUESTED_OPERATIONS), alias="requestedOperations")


class WorkerEventResponse(ApiModel):
    event_type: str = Field(alias="eventType")
    job_id: str = Field(alias="jobId")
    upload_id: str = Field(alias="uploadId")
    storage_key: str = Field(alias="storageKey")
    requested_operations: list[str] = Field(alias="requestedOperations")


class AnalysisJobResponse(ApiModel):
    job_id: str = Field(alias="jobId")
    type: str
    status: ImageAnalysisJobStatus
    progress: int
    upload_id: str = Field(alias="uploadId")
    storage_key: str = Field(alias="storageKey")
    original_file_name: str = Field(alias="originalFileName")
    content_type: str = Field(alias="contentType")
    requested_operations: list[str] = Field(alias="requestedOperations")
    result: Optional[dict[str, object]]
    error: Optional[str]
    created_at: Optional[datetime] = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(alias="updatedAt")
    worker_event: Optional[WorkerEventResponse] = Field(default=None, alias="workerEvent")


class WorkerRunResponse(ApiModel):
    processed: bool
    reason: str
    job_id: Optional[str] = Field(default=None, alias="jobId")
    status: Optional[ImageAnalysisJobStatus] = None
    progress: Optional[int] = None
    result: Optional[dict[str, object]] = None
    error: Optional[str] = None

    @classmethod
    def from_result(cls, result: ImageAnalysisWorkerResult) -> "WorkerRunResponse":
        return cls(
            processed=result.processed,
            reason=result.reason,
            jobId=result.job.id if result.job else None,
            status=result.job.status if result.job else None,
            progress=result.job.progress if result.job else None,
            result=result.job.result if result.job else None,
            error=result.job.error if result.job else None,
        )


def to_upload_url_response(ticket: ImageUploadTicket) -> UploadUrlResponse:
    return UploadUrlResponse(
        uploadId=ticket.id,
        uploadUrl=ticket.upload_url,
        method=ticket.method,
        storageKey=ticket.storage_key,
        expiresAt=ticket.expires_at,
        headers=ticket.headers,
    )


def to_upload_completion_response(ticket: ImageUploadTicket, stored_object: StoredUploadObject) -> UploadCompletionResponse:
    return UploadCompletionResponse(
        uploadId=ticket.id,
        uploaded=True,
        storageKey=stored_object.storage_key,
        contentType=stored_object.content_type,
        byteSize=stored_object.byte_size,
        checksumSha256=stored_object.checksum_sha256,
    )


def to_worker_event_response(event: WorkerEvent) -> WorkerEventResponse:
    return WorkerEventResponse(
        eventType=event.event_type,
        jobId=event.job_id,
        uploadId=event.upload_id,
        storageKey=event.storage_key,
        requestedOperations=list(event.requested_operations),
    )


def to_analysis_job_response(
    job: ImageAnalysisJob,
    worker_event: WorkerEvent | None = None,
) -> AnalysisJobResponse:
    return AnalysisJobResponse(
        jobId=job.id,
        type="closet_item_analysis",
        status=job.status,
        progress=job.progress,
        uploadId=job.upload_id,
        storageKey=job.storage_key,
        originalFileName=job.original_file_name,
        contentType=job.content_type,
        requestedOperations=list(job.requested_operations),
        result=job.result,
        error=job.error,
        createdAt=job.created_at,
        updatedAt=job.updated_at,
        workerEvent=to_worker_event_response(worker_event) if worker_event else None,
    )
