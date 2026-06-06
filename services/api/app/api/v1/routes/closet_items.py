from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import Response

from ....repositories.closet_items import ClosetItemAlreadyExistsError, ClosetItemNotFoundError, ClosetItemRepository
from ....repositories.image_analysis_jobs import ImageAnalysisJobNotFoundError, ImageUploadNotFoundError
from ..schemas.closet_items import (
    ClosetItemCreateRequest,
    ClosetItemResponse,
    ClosetItemUpdateRequest,
    to_closet_item_response,
)
from ..schemas.image_analysis import (
    AnalysisJobCreateRequest,
    AnalysisJobResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    to_analysis_job_response,
    to_upload_url_response,
)

router = APIRouter()


def _repository(request: Request) -> ClosetItemRepository:
    return request.app.state.closet_repository


def _image_analysis_repository(request: Request):
    return request.app.state.image_analysis_repository


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


@router.post("/analyze", response_model=AnalysisJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_analysis_job(payload: AnalysisJobCreateRequest, request: Request) -> AnalysisJobResponse:
    try:
        job, event = _image_analysis_repository(request).create_analysis_job(
            upload_id=payload.upload_id,
            requested_operations=tuple(payload.requested_operations),
        )
    except ImageUploadNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload ticket not found.") from error
    return to_analysis_job_response(job, worker_event=event)


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
