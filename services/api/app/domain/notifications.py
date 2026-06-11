from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time

from .enums import MorningRunStatus, PushDispatchStatus


@dataclass(frozen=True)
class NotificationSettings:
    id: str
    enabled: bool
    timezone: str
    weekday_notification_time: time
    weekend_notification_time: time | None
    location_label: str | None
    latitude: float | None
    longitude: float | None
    updated_at: datetime


@dataclass(frozen=True)
class MorningRecommendationRun:
    id: str
    run_date: str
    status: MorningRunStatus
    reason: str | None
    recommendation_id: str | None
    weather_snapshot: dict[str, object]
    created_at: datetime


@dataclass(frozen=True)
class PushDispatch:
    id: str
    recommendation_id: str
    status: PushDispatchStatus
    title: str
    body: str
    provider: str
    created_at: datetime

