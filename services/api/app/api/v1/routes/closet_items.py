import hashlib
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import Response

from ....repositories.closet_items import ClosetItemAlreadyExistsError, ClosetItemNotFoundError, ClosetItemRepository
from ....repositories.image_analysis_jobs import (
    ImageAnalysisJobNotFoundError,
    ImageUploadNotFoundError,
    ImageUploadNotReadyError,
)
from ....services.image_analysis_worker import process_next_image_analysis_job
from ..schemas.closet_items import (
    ClosetItemCreateRequest,
    ClosetItemResponse,
    ClosetItemUpdateRequest,
    to_closet_item_response,
)
from ..schemas.image_analysis import (
    AnalysisJobCreateRequest,
    AnalysisJobResponse,
    UploadCompletionResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    WorkerRunResponse,
    to_analysis_job_response,
    to_upload_completion_response,
    to_upload_url_response,
)

router = APIRouter()


def _repository(request: Request) -> ClosetItemRepository:
    return request.app.state.closet_repository


def _image_analysis_repository(request: Request):
    return request.app.state.image_analysis_repository


def _upload_storage(request: Request):
    return request.app.state.upload_storage


@router.get("", response_model=list[ClosetItemResponse])
def list_closet_items(request: Request) -> list[ClosetItemResponse]:
    return [to_closet_item_response(item) for item in _repository(request).list()]


@router.post("", response_model=ClosetItemResponse, status_code=status.HTTP_201_CREATED)
def create_closet_item(payload: ClosetItemCreateRequest, request: Request) -> ClosetItemResponse:
    try:
        item = _repository(request).create(payload.to_domain())
    except ClosetItemAlreadyExistsError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Closet item already exists.") from error
    return to_closet_item_response(item)


@router.post("/uploads", response_model=UploadUrlResponse, status_code=status.HTTP_201_CREATED)
def create_upload_url(payload: UploadUrlRequest, request: Request) -> UploadUrlResponse:
    ticket = _image_analysis_repository(request).create_upload_ticket(
        file_name=payload.file_name,
        content_type=payload.content_type,
        byte_size=payload.byte_size,
        checksum_sha256=payload.checksum_sha256,
    )
    return to_upload_url_response(ticket)


@router.put("/uploads/{upload_id}/object", response_model=UploadCompletionResponse)
async def upload_object(
    upload_id: str,
    request: Request,
    content_type: Optional[str] = Header(default=None),
) -> UploadCompletionResponse:
    try:
        ticket = _image_analysis_repository(request).get_upload_ticket(upload_id)
    except ImageUploadNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload ticket not found.") from error

    normalized_content_type = _normalize_content_type(content_type)
    if normalized_content_type != ticket.content_type.lower():
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload content type does not match ticket.",
        )

    body = await request.body()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload body is empty.")
    if ticket.byte_size is not None and len(body) != ticket.byte_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload byte size does not match ticket.")
    if ticket.checksum_sha256 is not None and hashlib.sha256(body).hexdigest() != ticket.checksum_sha256:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload checksum does not match ticket.")

    stored_object = _upload_storage(request).save(
        storage_key=ticket.storage_key,
        content_type=ticket.content_type,
        data=body,
    )
    _image_analysis_repository(request).mark_upload_completed(
        upload_id,
        byte_size=stored_object.byte_size,
        checksum_sha256=stored_object.checksum_sha256,
    )

    return to_upload_completion_response(ticket, stored_object)


@router.post("/analyze", response_model=AnalysisJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_analysis_job(payload: AnalysisJobCreateRequest, request: Request) -> AnalysisJobResponse:
    try:
        ticket = _image_analysis_repository(request).get_upload_ticket(payload.upload_id)
        if ticket.uploaded_at is None or not _upload_storage(request).exists(ticket.storage_key):
            raise ImageUploadNotReadyError(payload.upload_id)
        job, event = _image_analysis_repository(request).create_analysis_job(
            upload_id=payload.upload_id,
            requested_operations=tuple(payload.requested_operations),
        )
    except ImageUploadNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload ticket not found.") from error
    except ImageUploadNotReadyError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload object is not ready for analysis.",
        ) from error
    return to_analysis_job_response(job, worker_event=event)


@router.post("/jobs/process-next", response_model=WorkerRunResponse)
def process_next_analysis_job(request: Request) -> WorkerRunResponse:
    result = process_next_image_analysis_job(
        _image_analysis_repository(request),
        _upload_storage(request),
        request.app.state.image_analysis_provider,
    )
    return WorkerRunResponse.from_result(result)


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
def get_analysis_job(job_id: str, request: Request) -> AnalysisJobResponse:
    try:
        job = _image_analysis_repository(request).get_job(job_id)
    except ImageAnalysisJobNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found.") from error
    return to_analysis_job_response(job)


@router.get("/{item_id}", response_model=ClosetItemResponse)
def get_closet_item(item_id: str, request: Request) -> ClosetItemResponse:
    try:
        item = _repository(request).get(item_id)
    except ClosetItemNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Closet item not found.") from error
    return to_closet_item_response(item)


@router.patch("/{item_id}", response_model=ClosetItemResponse)
def update_closet_item(
    item_id: str,
    payload: ClosetItemUpdateRequest,
    request: Request,
) -> ClosetItemResponse:
    try:
        item = _repository(request).update(item_id, **payload.to_changes())
    except ClosetItemNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Closet item not found.") from error
    return to_closet_item_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_closet_item(item_id: str, request: Request) -> Response:
    try:
        _repository(request).delete(item_id)
    except ClosetItemNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Closet item not found.") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _normalize_content_type(content_type: Optional[str]) -> str:
    return (content_type or "").split(";", maxsplit=1)[0].strip().lower()
