from __future__ import annotations

from datetime import datetime, time
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field

from ....domain import NotificationSettings, PushDispatch, PushDispatchStatus
from ....services.morning_scheduler import MorningSchedulerResult
from .recommendations import WeatherPayload


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, use_enum_values=False)


class NotificationSettingsUpdateRequest(ApiModel):
    enabled: Optional[bool] = None
    timezone: Optional[str] = None
    weekday_notification_time: Optional[str] = Field(default=None, alias="weekdayNotificationTime")
    weekend_notification_time: Optional[str] = Field(default=None, alias="weekendNotificationTime")
    location_label: Optional[str] = Field(default=None, alias="locationLabel")
    latitude: Annotated[Optional[float], Field(ge=-90, le=90)] = None
    longitude: Annotated[Optional[float], Field(ge=-180, le=180)] = None

    def to_changes(self) -> dict[str, object]:
        changes: dict[str, object] = {}
        fields = self.model_fields_set
        for field_name in ("enabled", "timezone", "location_label", "latitude", "longitude"):
            if field_name in fields:
                changes[field_name] = getattr(self, field_name)
        if "weekday_notification_time" in fields and self.weekday_notification_time is not None:
            changes["weekday_notification_time"] = _parse_time(self.weekday_notification_time)
        if "weekend_notification_time" in fields:
            changes["weekend_notification_time"] = (
                _parse_time(self.weekend_notification_time) if self.weekend_notification_time else None
            )
        return changes


class NotificationSettingsResponse(ApiModel):
    id: str
    enabled: bool
    timezone: str
    weekday_notification_time: str = Field(alias="weekdayNotificationTime")
    weekend_notification_time: Optional[str] = Field(alias="weekendNotificationTime")
    location_label: Optional[str] = Field(alias="locationLabel")
    latitude: Optional[float]
    longitude: Optional[float]
    updated_at: datetime = Field(alias="updatedAt")

    @classmethod
    def from_domain(cls, settings: NotificationSettings) -> "NotificationSettingsResponse":
        return cls(
            id=settings.id,
            enabled=settings.enabled,
            timezone=settings.timezone,
            weekdayNotificationTime=_format_time(settings.weekday_notification_time),
            weekendNotificationTime=_format_time(settings.weekend_notification_time)
            if settings.weekend_notification_time
            else None,
            locationLabel=settings.location_label,
            latitude=settings.latitude,
            longitude=settings.longitude,
            updatedAt=settings.updated_at,
        )


class MorningRecommendationRunRequest(ApiModel):
    now: Optional[datetime] = None
    weather: Optional[WeatherPayload] = None


class PushDispatchResponse(ApiModel):
    dispatch_id: str = Field(alias="dispatchId")
    recommendation_id: str = Field(alias="recommendationId")
    status: PushDispatchStatus
    title: str
    body: str
    provider: str
    created_at: datetime = Field(alias="createdAt")

    @classmethod
    def from_domain(cls, dispatch: PushDispatch) -> "PushDispatchResponse":
        return cls(
            dispatchId=dispatch.id,
            recommendationId=dispatch.recommendation_id,
            status=dispatch.status,
            title=dispatch.title,
            body=dispatch.body,
            provider=dispatch.provider,
            createdAt=dispatch.created_at,
        )


class MorningRecommendationRunResponse(ApiModel):
    created: bool
    reason: str
    run_id: Optional[str] = Field(default=None, alias="runId")
    run_date: Optional[str] = Field(default=None, alias="runDate")
    recommendation_id: Optional[str] = Field(default=None, alias="recommendationId")
    weather_source: str = Field(alias="weatherSource")
    push_dispatch: Optional[PushDispatchResponse] = Field(default=None, alias="pushDispatch")

    @classmethod
    def from_result(cls, result: MorningSchedulerResult) -> "MorningRecommendationRunResponse":
        return cls(
            created=result.created,
            reason=result.reason,
            runId=result.run.id if result.run else None,
            runDate=result.run.run_date if result.run else None,
            recommendationId=result.recommendation_id,
            weatherSource=result.weather_source,
            pushDispatch=PushDispatchResponse.from_domain(result.push_dispatch) if result.push_dispatch else None,
        )


def _format_time(value: time) -> str:
    return value.strftime("%H:%M")


def _parse_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))

