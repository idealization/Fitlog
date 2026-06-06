from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from ..domain import ClosetItem


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

