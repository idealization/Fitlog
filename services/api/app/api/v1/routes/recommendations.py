from fastapi import APIRouter, HTTPException

from ....domain import generate_outfit_recommendations
from ....repositories.demo_data import demo_closet_items, demo_trend_signals, demo_weather
from ..schemas.recommendations import RecommendationRequest, RecommendationResponse, to_candidate_response

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
def create_recommendation(payload: RecommendationRequest) -> RecommendationResponse:
    items = [item.to_domain() for item in payload.items]
    if payload.use_demo_closet:
        items.extend(demo_closet_items())

    if not items:
        raise HTTPException(status_code=400, detail="At least one closet item is required.")

    candidates = generate_outfit_recommendations(
        items=items,
        weather=payload.weather.to_domain(),
        request=payload.style_request.to_domain(),
        trends=[trend.to_domain() for trend in payload.trends],
        limit=payload.limit,
    )

    return RecommendationResponse(candidates=[to_candidate_response(candidate) for candidate in candidates])

