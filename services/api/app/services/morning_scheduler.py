from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..domain import (
    MorningRecommendationRun,
    MorningRunStatus,
    NotificationSettings,
    PushDispatch,
    RecommendationStatus,
    StyleRequest,
    TrendLevel,
    WeatherSnapshot,
    generate_outfit_recommendations,
)
from ..repositories.closet_items import ClosetItemRepository
from ..repositories.notifications import NotificationRepository
from ..repositories.recommendations import RecommendationRepository


@dataclass(frozen=True)
class MorningSchedulerResult:
    created: bool
    reason: str
    run: MorningRecommendationRun | None = None
    recommendation_id: str | None = None
    recommendation_status: RecommendationStatus | None = None
    push_dispatch: PushDispatch | None = None
    weather_source: str = "fallback"


def run_due_morning_recommendation(
    now: datetime,
    weather: WeatherSnapshot | None,
    notification_repository: NotificationRepository,
    closet_repository: ClosetItemRepository,
    recommendation_repository: RecommendationRepository,
) -> MorningSchedulerResult:
    settings = notification_repository.get_settings()
    local_now = _localize(now, settings.timezone)
    run_date = local_now.date().isoformat()
    scheduled_time = _scheduled_time(settings, local_now)

    if not settings.enabled:
        return MorningSchedulerResult(created=False, reason="disabled")
    if local_now.time() < scheduled_time:
        return MorningSchedulerResult(created=False, reason="not_due")

    existing_run = notification_repository.get_run_for_date(run_date)
    if existing_run and existing_run.recommendation_id:
        return MorningSchedulerResult(
            created=False,
            reason="already_created",
            run=existing_run,
            recommendation_id=existing_run.recommendation_id,
        )

    items = closet_repository.list()
    active_weather = weather or fallback_weather_snapshot(local_now)
    weather_source = "provided" if weather else "fallback"
    weather_payload = weather_snapshot_payload(active_weather, weather_source)

    if not items:
        run = notification_repository.create_run(
            run_date=run_date,
            status=MorningRunStatus.SKIPPED,
            reason="no_closet_items",
            weather_snapshot=weather_payload,
        )
        return MorningSchedulerResult(created=False, reason="no_closet_items", run=run, weather_source=weather_source)

    style_request = StyleRequest(
        occasion="daily",
        mood_tags=(),
        comfort_priority="medium",
        trend_level=TrendLevel.BALANCED,
    )
    candidates = generate_outfit_recommendations(
        items=items,
        weather=active_weather,
        request=style_request,
        trends=[],
        limit=1,
    )

    if not candidates:
        run = notification_repository.create_run(
            run_date=run_date,
            status=MorningRunStatus.SKIPPED,
            reason="no_candidates",
            weather_snapshot=weather_payload,
        )
        return MorningSchedulerResult(created=False, reason="no_candidates", run=run, weather_source=weather_source)

    recommendation = recommendation_repository.create(
        request_payload={
            "recommendationType": "morning",
            "generatedAt": local_now.isoformat(),
            "weather": weather_payload,
            "styleRequest": {
                "occasion": style_request.occasion,
                "moodTags": list(style_request.mood_tags),
                "trendLevel": style_request.trend_level.value,
            },
        },
        candidates=candidates,
    )
    run = notification_repository.create_run(
        run_date=run_date,
        status=MorningRunStatus.CREATED,
        reason=None,
        recommendation_id=recommendation.id,
        weather_snapshot=weather_payload,
    )
    dispatch = notification_repository.create_push_dispatch(
        recommendation_id=recommendation.id,
        title="오늘의 Fitlog 추천",
        body=_push_body(active_weather),
    )

    return MorningSchedulerResult(
        created=True,
        reason="created",
        run=run,
        recommendation_id=recommendation.id,
        recommendation_status=recommendation.status,
        push_dispatch=dispatch,
        weather_source=weather_source,
    )


def fallback_weather_snapshot(now: datetime) -> WeatherSnapshot:
    month = now.month
    if month in {12, 1, 2}:
        temperature = 3
    elif month in {6, 7, 8}:
        temperature = 28
    elif month in {3, 4, 5}:
        temperature = 18
    else:
        temperature = 15

    return WeatherSnapshot(
        temperature_c=temperature,
        feels_like_c=temperature,
        precipitation_probability=0.0,
    )


def weather_snapshot_payload(weather: WeatherSnapshot, source: str) -> dict[str, object]:
    return {
        "source": source,
        "temperatureC": weather.temperature_c,
        "feelsLikeC": weather.feels_like_c,
        "precipitationProbability": weather.precipitation_probability,
        "precipitationType": weather.precipitation_type.value,
        "humidity": weather.humidity,
        "windSpeedMps": weather.wind_speed_mps,
        "uvIndex": weather.uv_index,
        "airQuality": weather.air_quality,
    }


def _scheduled_time(settings: NotificationSettings, local_now: datetime) -> time:
    if local_now.weekday() >= 5 and settings.weekend_notification_time:
        return settings.weekend_notification_time
    return settings.weekday_notification_time


def _localize(value: datetime, timezone_name: str) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        zone = timezone.utc
    return value.astimezone(zone)


def _push_body(weather: WeatherSnapshot) -> str:
    return f"체감 {weather.feels_like_c:.0f}도 날씨에 맞춘 오늘의 코디를 준비했어요."

