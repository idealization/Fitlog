from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import Response

from ....repositories.closet_items import ClosetItemAlreadyExistsError, ClosetItemNotFoundError, ClosetItemRepository
from ..schemas.closet_items import (
    ClosetItemCreateRequest,
    ClosetItemResponse,
    ClosetItemUpdateRequest,
    to_closet_item_response,
)

router = APIRouter()


def _repository(request: Request) -> ClosetItemRepository:
    return request.app.state.closet_repository


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

