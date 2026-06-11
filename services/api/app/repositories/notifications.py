from __future__ import annotations

from dataclasses import replace
from datetime import datetime, time, timezone
from typing import Protocol
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from ..db.models import MorningRecommendationRunRecord, NotificationSettingsRecord, PushDispatchRecord
from ..db.session import session_scope
from ..domain import (
    MorningRecommendationRun,
    MorningRunStatus,
    NotificationSettings,
    PushDispatch,
    PushDispatchStatus,
)

DEFAULT_NOTIFICATION_SETTINGS_ID = "default"


class NotificationRepository(Protocol):
    def get_settings(self) -> NotificationSettings:
        ...

    def update_settings(self, **changes: object) -> NotificationSettings:
        ...

    def get_run_for_date(self, run_date: str) -> MorningRecommendationRun | None:
        ...

    def create_run(
        self,
        run_date: str,
        status: MorningRunStatus,
        weather_snapshot: dict[str, object],
        recommendation_id: str | None = None,
        reason: str | None = None,
    ) -> MorningRecommendationRun:
        ...

    def create_push_dispatch(
        self,
        recommendation_id: str,
        title: str,
        body: str,
        provider: str = "placeholder",
    ) -> PushDispatch:
        ...


class InMemoryNotificationRepository:
    def __init__(self):
        self._settings = _default_settings()
        self._runs: dict[str, MorningRecommendationRun] = {}
        self._dispatches: dict[str, PushDispatch] = {}

    def get_settings(self) -> NotificationSettings:
        return self._settings

    def update_settings(self, **changes: object) -> NotificationSettings:
        self._settings = replace(self._settings, **changes, updated_at=_now())
        return self._settings

    def get_run_for_date(self, run_date: str) -> MorningRecommendationRun | None:
        return self._runs.get(run_date)

    def create_run(
        self,
        run_date: str,
        status: MorningRunStatus,
        weather_snapshot: dict[str, object],
        recommendation_id: str | None = None,
        reason: str | None = None,
    ) -> MorningRecommendationRun:
        run = MorningRecommendationRun(
            id=uuid4().hex,
            run_date=run_date,
            status=status,
            reason=reason,
            recommendation_id=recommendation_id,
            weather_snapshot=weather_snapshot,
            created_at=_now(),
        )
        self._runs[run_date] = run
        return run

    def create_push_dispatch(
        self,
        recommendation_id: str,
        title: str,
        body: str,
        provider: str = "placeholder",
    ) -> PushDispatch:
        dispatch = PushDispatch(
            id=uuid4().hex,
            recommendation_id=recommendation_id,
            status=PushDispatchStatus.QUEUED,
            title=title,
            body=body,
            provider=provider,
            created_at=_now(),
        )
        self._dispatches[dispatch.id] = dispatch
        return dispatch


class SqlAlchemyNotificationRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def get_settings(self) -> NotificationSettings:
        with session_scope(self._session_factory) as session:
            record = session.get(NotificationSettingsRecord, DEFAULT_NOTIFICATION_SETTINGS_ID)
            if record is None:
                record = _settings_to_record(_default_settings())
                session.add(record)
                session.flush()
            return _settings_record_to_domain(record)

    def update_settings(self, **changes: object) -> NotificationSettings:
        with session_scope(self._session_factory) as session:
            record = session.get(NotificationSettingsRecord, DEFAULT_NOTIFICATION_SETTINGS_ID)
            if record is None:
                record = _settings_to_record(_default_settings())
                session.add(record)
            for field_name, value in changes.items():
                setattr(record, field_name, _serialize_settings_value(value))
            record.updated_at = _now()
            session.flush()
            return _settings_record_to_domain(record)

    def get_run_for_date(self, run_date: str) -> MorningRecommendationRun | None:
        with session_scope(self._session_factory) as session:
            record = (
                session.query(MorningRecommendationRunRecord)
                .filter(MorningRecommendationRunRecord.run_date == run_date)
                .order_by(MorningRecommendationRunRecord.created_at.desc())
                .first()
            )
            return _run_record_to_domain(record) if record else None

    def create_run(
        self,
        run_date: str,
        status: MorningRunStatus,
        weather_snapshot: dict[str, object],
        recommendation_id: str | None = None,
        reason: str | None = None,
    ) -> MorningRecommendationRun:
        run = MorningRecommendationRun(
            id=uuid4().hex,
            run_date=run_date,
            status=status,
            reason=reason,
            recommendation_id=recommendation_id,
            weather_snapshot=weather_snapshot,
            created_at=_now(),
        )
        with session_scope(self._session_factory) as session:
            session.add(_run_to_record(run))
        return run

    def create_push_dispatch(
        self,
        recommendation_id: str,
        title: str,
        body: str,
        provider: str = "placeholder",
    ) -> PushDispatch:
        dispatch = PushDispatch(
            id=uuid4().hex,
            recommendation_id=recommendation_id,
            status=PushDispatchStatus.QUEUED,
            title=title,
            body=body,
            provider=provider,
            created_at=_now(),
        )
        with session_scope(self._session_factory) as session:
            session.add(_dispatch_to_record(dispatch))
        return dispatch


def _default_settings() -> NotificationSettings:
    return NotificationSettings(
        id=DEFAULT_NOTIFICATION_SETTINGS_ID,
        enabled=False,
        timezone="Asia/Seoul",
        weekday_notification_time=time(hour=8, minute=0),
        weekend_notification_time=time(hour=9, minute=0),
        location_label=None,
        latitude=None,
        longitude=None,
        updated_at=_now(),
    )


def _settings_to_record(settings: NotificationSettings) -> NotificationSettingsRecord:
    return NotificationSettingsRecord(
        id=settings.id,
        enabled=settings.enabled,
        timezone=settings.timezone,
        weekday_notification_time=_format_time(settings.weekday_notification_time),
        weekend_notification_time=_format_time(settings.weekend_notification_time)
        if settings.weekend_notification_time
        else None,
        location_label=settings.location_label,
        latitude=settings.latitude,
        longitude=settings.longitude,
        updated_at=settings.updated_at,
    )


def _settings_record_to_domain(record: NotificationSettingsRecord) -> NotificationSettings:
    return NotificationSettings(
        id=record.id,
        enabled=record.enabled,
        timezone=record.timezone,
        weekday_notification_time=_parse_time(record.weekday_notification_time),
        weekend_notification_time=_parse_time(record.weekend_notification_time) if record.weekend_notification_time else None,
        location_label=record.location_label,
        latitude=record.latitude,
        longitude=record.longitude,
        updated_at=record.updated_at,
    )


def _run_to_record(run: MorningRecommendationRun) -> MorningRecommendationRunRecord:
    return MorningRecommendationRunRecord(
        id=run.id,
        run_date=run.run_date,
        status=run.status.value,
        reason=run.reason,
        recommendation_id=run.recommendation_id,
        weather_snapshot=run.weather_snapshot,
        created_at=run.created_at,
    )


def _run_record_to_domain(record: MorningRecommendationRunRecord) -> MorningRecommendationRun:
    return MorningRecommendationRun(
        id=record.id,
        run_date=record.run_date,
        status=MorningRunStatus(record.status),
        reason=record.reason,
        recommendation_id=record.recommendation_id,
        weather_snapshot=record.weather_snapshot,
        created_at=record.created_at,
    )


def _dispatch_to_record(dispatch: PushDispatch) -> PushDispatchRecord:
    return PushDispatchRecord(
        id=dispatch.id,
        recommendation_id=dispatch.recommendation_id,
        status=dispatch.status.value,
        title=dispatch.title,
        body=dispatch.body,
        provider=dispatch.provider,
        created_at=dispatch.created_at,
    )


def _format_time(value: time) -> str:
    return value.strftime("%H:%M")


def _parse_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def _serialize_settings_value(value: object) -> object:
    if isinstance(value, time):
        return _format_time(value)
    return value


def _now() -> datetime:
    return datetime.now(timezone.utc)

