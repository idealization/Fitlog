from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from ..db.models import ClosetItemRecord
from ..db.session import session_scope
from ..domain import Category, ClosetItem, Formality, ItemStatus, Season, Thickness


class ClosetItemNotFoundError(Exception):
    pass


class ClosetItemAlreadyExistsError(Exception):
    pass


class ClosetItemRepository(Protocol):
    def list(self) -> list[ClosetItem]:
        ...

    def get(self, item_id: str) -> ClosetItem:
        ...

    def create(self, item: ClosetItem) -> ClosetItem:
        ...

    def update(self, item_id: str, **changes: object) -> ClosetItem:
        ...

    def delete(self, item_id: str) -> None:
        ...


class InMemoryClosetItemRepository:
    def __init__(self, initial_items: list[ClosetItem] | None = None):
        self._items: dict[str, ClosetItem] = {}
        for item in initial_items or []:
            self._items[item.id] = item

    def list(self) -> list[ClosetItem]:
        return sorted(self._items.values(), key=lambda item: item.name.lower())

    def get(self, item_id: str) -> ClosetItem:
        try:
            return self._items[item_id]
        except KeyError as error:
            raise ClosetItemNotFoundError(item_id) from error

    def create(self, item: ClosetItem) -> ClosetItem:
        if item.id in self._items:
            raise ClosetItemAlreadyExistsError(item.id)
        self._items[item.id] = item
        return item

    def update(self, item_id: str, **changes: object) -> ClosetItem:
        current = self.get(item_id)
        updated = replace(current, **changes)
        self._items[item_id] = updated
        return updated

    def delete(self, item_id: str) -> None:
        self.get(item_id)
        del self._items[item_id]


class SqlAlchemyClosetItemRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def list(self) -> list[ClosetItem]:
        with session_scope(self._session_factory) as session:
            records = session.query(ClosetItemRecord).order_by(ClosetItemRecord.name.asc()).all()
            return [_record_to_domain(record) for record in records]

    def get(self, item_id: str) -> ClosetItem:
        with session_scope(self._session_factory) as session:
            record = session.get(ClosetItemRecord, item_id)
            if record is None:
                raise ClosetItemNotFoundError(item_id)
            return _record_to_domain(record)

    def create(self, item: ClosetItem) -> ClosetItem:
        with session_scope(self._session_factory) as session:
            record = _domain_to_record(item)
            session.add(record)
            try:
                session.flush()
            except IntegrityError as error:
                raise ClosetItemAlreadyExistsError(item.id) from error
            return _record_to_domain(record)

    def update(self, item_id: str, **changes: object) -> ClosetItem:
        with session_scope(self._session_factory) as session:
            record = session.get(ClosetItemRecord, item_id)
            if record is None:
                raise ClosetItemNotFoundError(item_id)
            for field_name, value in changes.items():
                setattr(record, field_name, _serialize_value(value))
            session.flush()
            return _record_to_domain(record)

    def delete(self, item_id: str) -> None:
        with session_scope(self._session_factory) as session:
            record = session.get(ClosetItemRecord, item_id)
            if record is None:
                raise ClosetItemNotFoundError(item_id)
            session.delete(record)


def _domain_to_record(item: ClosetItem) -> ClosetItemRecord:
    return ClosetItemRecord(
        id=item.id,
        name=item.name,
        category=item.category.value,
        sub_type=item.sub_type,
        seasons=[season.value for season in item.seasons],
        style_tags=list(item.style_tags),
        colors=list(item.colors),
        thickness=item.thickness.value,
        formality=item.formality.value,
        status=item.status.value,
        warmth=item.warmth,
        rain_safe=item.rain_safe,
        breathability=item.breathability,
        wear_count=item.wear_count,
        last_worn_days_ago=item.last_worn_days_ago,
    )


def _record_to_domain(record: ClosetItemRecord) -> ClosetItem:
    return ClosetItem(
        id=record.id,
        name=record.name,
        category=Category(record.category),
        sub_type=record.sub_type,
        seasons=tuple(Season(season) for season in record.seasons),
        style_tags=tuple(record.style_tags),
        colors=tuple(record.colors),
        thickness=Thickness(record.thickness),
        formality=Formality(record.formality),
        status=ItemStatus(record.status),
        warmth=record.warmth,
        rain_safe=record.rain_safe,
        breathability=record.breathability,
        wear_count=record.wear_count,
        last_worn_days_ago=record.last_worn_days_ago,
    )


def _serialize_value(value: object) -> object:
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value
