from datetime import datetime, timezone

from fastapi import APIRouter, Request

from ....services.morning_scheduler import run_due_morning_recommendation
from ..schemas.notifications import (
    MorningRecommendationRunRequest,
    MorningRecommendationRunResponse,
    NotificationSettingsResponse,
    NotificationSettingsUpdateRequest,
)

router = APIRouter()


@router.get("/notification-settings", response_model=NotificationSettingsResponse)
def get_notification_settings(request: Request) -> NotificationSettingsResponse:
    settings = request.app.state.notification_repository.get_settings()
    return NotificationSettingsResponse.from_domain(settings)


@router.patch("/notification-settings", response_model=NotificationSettingsResponse)
def update_notification_settings(
    payload: NotificationSettingsUpdateRequest,
    request: Request,
) -> NotificationSettingsResponse:
    settings = request.app.state.notification_repository.update_settings(**payload.to_changes())
    return NotificationSettingsResponse.from_domain(settings)


@router.post("/morning-recommendations/run-due", response_model=MorningRecommendationRunResponse)
def run_due_morning_recommendation_endpoint(
    payload: MorningRecommendationRunRequest,
    request: Request,
) -> MorningRecommendationRunResponse:
    result = run_due_morning_recommendation(
        now=payload.now or datetime.now(timezone.utc),
        weather=payload.weather.to_domain() if payload.weather else None,
        notification_repository=request.app.state.notification_repository,
        closet_repository=request.app.state.closet_repository,
        recommendation_repository=request.app.state.recommendation_repository,
    )
    return MorningRecommendationRunResponse.from_result(result)

