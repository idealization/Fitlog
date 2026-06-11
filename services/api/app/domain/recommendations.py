from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .enums import RecommendationStatus
from .models import OutfitCandidate


@dataclass(frozen=True)
class StoredOutfitCandidate:
    id: str
    recommendation_id: str
    rank: int
    item_ids: tuple[str, ...]
    score: float
    reasons: tuple[str, ...]
    items_snapshot: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class StoredRecommendation:
    id: str
    status: RecommendationStatus
    request_payload: dict[str, object]
    candidates: tuple[StoredOutfitCandidate, ...]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RecommendationFeedback:
    id: str
    recommendation_id: str
    feedback_type: str
    note: str | None
    created_at: datetime


@dataclass(frozen=True)
class WearLog:
    id: str
    recommendation_id: str
    item_ids: tuple[str, ...]
    created_at: datetime


def outfit_candidate_snapshot(candidate: OutfitCandidate) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "id": item.id,
            "name": item.name,
            "category": item.category.value,
            "subType": item.sub_type,
            "colors": list(item.colors),
            "styleTags": list(item.style_tags),
        }
        for item in candidate.items
    )
