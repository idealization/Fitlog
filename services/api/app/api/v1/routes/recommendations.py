from fastapi import APIRouter, HTTPException, Request, status

from ....domain import generate_outfit_recommendations
from ....repositories.demo_data import demo_closet_items, demo_trend_signals, demo_weather
from ....repositories.recommendations import RecommendationNotFoundError
from ..schemas.recommendations import (
    RecommendationFeedbackRequest,
    RecommendationFeedbackResponse,
    RecommendationRequest,
    RecommendationResponse,
    WearLogResponse,
)

router = APIRouter()


@router.get("/demo", response_model=RecommendationResponse)
def demo_recommendations() -> RecommendationResponse:
    candidates = generate_outfit_recommendations(
        items=demo_closet_items(),
        weather=demo_weather(),
        request=RecommendationRequest.demo_style_request(),
        trends=demo_trend_signals(),
    )
    return RecommendationResponse.from_candidates(candidates)


@router.post("", response_model=RecommendationResponse)
def create_recommendation(payload: RecommendationRequest, request: Request) -> RecommendationResponse:
    items = [item.to_domain() for item in payload.items]
    if payload.use_demo_closet:
        items.extend(demo_closet_items())
    if not items:
        items.extend(request.app.state.closet_repository.list())

    if not items:
        raise HTTPException(status_code=400, detail="At least one closet item is required.")

    candidates = generate_outfit_recommendations(
        items=items,
        weather=payload.weather.to_domain(),
        request=payload.style_request.to_domain(),
        trends=[trend.to_domain() for trend in payload.trends],
        limit=payload.limit,
    )

    recommendation = request.app.state.recommendation_repository.create(
        request_payload=payload.model_dump(mode="json", by_alias=True),
        candidates=candidates,
    )
    return RecommendationResponse.from_stored(recommendation)


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation(recommendation_id: str, request: Request) -> RecommendationResponse:
    try:
        recommendation = request.app.state.recommendation_repository.get(recommendation_id)
    except RecommendationNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.") from error
    return RecommendationResponse.from_stored(recommendation)


@router.post("/{recommendation_id}/feedback", response_model=RecommendationFeedbackResponse)
def add_feedback(
    recommendation_id: str,
    payload: RecommendationFeedbackRequest,
    request: Request,
) -> RecommendationFeedbackResponse:
    try:
        feedback = request.app.state.recommendation_repository.add_feedback(
            recommendation_id=recommendation_id,
            feedback_type=payload.feedback_type,
            note=payload.note,
        )
    except RecommendationNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.") from error
    return RecommendationFeedbackResponse.from_domain(feedback)


@router.post("/{recommendation_id}/save", response_model=RecommendationResponse)
def save_recommendation(recommendation_id: str, request: Request) -> RecommendationResponse:
    try:
        recommendation = request.app.state.recommendation_repository.save(recommendation_id)
    except RecommendationNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.") from error
    return RecommendationResponse.from_stored(recommendation)


@router.post("/{recommendation_id}/wear", response_model=WearLogResponse)
def mark_recommendation_worn(recommendation_id: str, request: Request) -> WearLogResponse:
    try:
        _, wear_log = request.app.state.recommendation_repository.mark_worn(recommendation_id)
    except RecommendationNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.") from error
    return WearLogResponse.from_domain(wear_log)
