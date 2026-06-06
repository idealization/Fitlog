from __future__ import annotations

from dataclasses import dataclass, field

from .enums import Category, Formality, ItemStatus, PrecipitationType, Season, Thickness, TrendLevel


@dataclass(frozen=True)
class ClosetItem:
    id: str
    name: str
    category: Category
    sub_type: str
    seasons: tuple[Season, ...]
    style_tags: tuple[str, ...]
    colors: tuple[str, ...]
    thickness: Thickness = Thickness.MEDIUM
    formality: Formality = Formality.CASUAL
    status: ItemStatus = ItemStatus.AVAILABLE
    warmth: int = 5
    rain_safe: bool = False
    breathability: int = 5
    wear_count: int = 0
    last_worn_days_ago: int | None = None


@dataclass(frozen=True)
class WeatherSnapshot:
    temperature_c: float
    feels_like_c: float
    precipitation_probability: float
    precipitation_type: PrecipitationType = PrecipitationType.NONE
    humidity: float = 0.5
    wind_speed_mps: float = 0.0
    uv_index: float | None = None
    air_quality: str | None = None


@dataclass(frozen=True)
class StyleRequest:
    occasion: str | None = None
    mood_tags: tuple[str, ...] = ()
    formality: Formality | None = None
    comfort_priority: str = "medium"
    preferred_colors: tuple[str, ...] = ()
    excluded_colors: tuple[str, ...] = ()
    avoid_tags: tuple[str, ...] = ()
    fixed_item_ids: tuple[str, ...] = ()
    excluded_item_ids: tuple[str, ...] = ()
    trend_level: TrendLevel = TrendLevel.BALANCED


@dataclass(frozen=True)
class TrendSignal:
    tag: str
    strength: float
    region: str | None = None
    season: Season | None = None


@dataclass(frozen=True)
class OutfitCandidate:
    items: tuple[ClosetItem, ...]
    score: float
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def item_ids(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.items)

