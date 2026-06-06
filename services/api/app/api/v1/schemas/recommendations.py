from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field

from ....domain import (
    Category,
    ClosetItem,
    Formality,
    ItemStatus,
    OutfitCandidate,
    PrecipitationType,
    Season,
    StyleRequest,
    Thickness,
    TrendLevel,
    TrendSignal,
    WeatherSnapshot,
)


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, use_enum_values=False)


class ClosetItemPayload(ApiModel):
    id: str
    name: str
    category: Category
    sub_type: str = Field(alias="subType")
    seasons: list[Season]
    style_tags: list[str] = Field(default_factory=list, alias="styleTags")
    colors: list[str] = Field(default_factory=list)
    thickness: Thickness = Thickness.MEDIUM
    formality: Formality = Formality.CASUAL
    status: ItemStatus = ItemStatus.AVAILABLE
    warmth: Annotated[int, Field(ge=0, le=10)] = 5
    rain_safe: bool = Field(default=False, alias="rainSafe")
    breathability: Annotated[int, Field(ge=0, le=10)] = 5
    wear_count: Annotated[int, Field(ge=0)] = Field(default=0, alias="wearCount")
    last_worn_days_ago: Annotated[Optional[int], Field(ge=0)] = Field(default=None, alias="lastWornDaysAgo")

    def to_domain(self) -> ClosetItem:
        return ClosetItem(
            id=self.id,
            name=self.name,
            category=self.category,
            sub_type=self.sub_type,
            seasons=tuple(self.seasons),
            style_tags=tuple(self.style_tags),
            colors=tuple(self.colors),
            thickness=self.thickness,
            formality=self.formality,
            status=self.status,
            warmth=self.warmth,
            rain_safe=self.rain_safe,
            breathability=self.breathability,
            wear_count=self.wear_count,
            last_worn_days_ago=self.last_worn_days_ago,
        )


class WeatherPayload(ApiModel):
    temperature_c: float = Field(alias="temperatureC")
    feels_like_c: float = Field(alias="feelsLikeC")
    precipitation_probability: Annotated[float, Field(ge=0, le=1)] = Field(alias="precipitationProbability")
    precipitation_type: PrecipitationType = Field(default=PrecipitationType.NONE, alias="precipitationType")
    humidity: Annotated[float, Field(ge=0, le=1)] = 0.5
    wind_speed_mps: Annotated[float, Field(ge=0)] = Field(default=0.0, alias="windSpeedMps")
    uv_index: Annotated[Optional[float], Field(ge=0)] = Field(default=None, alias="uvIndex")
    air_quality: Optional[str] = Field(default=None, alias="airQuality")

    def to_domain(self) -> WeatherSnapshot:
        return WeatherSnapshot(
            temperature_c=self.temperature_c,
            feels_like_c=self.feels_like_c,
            precipitation_probability=self.precipitation_probability,
            precipitation_type=self.precipitation_type,
            humidity=self.humidity,
            wind_speed_mps=self.wind_speed_mps,
            uv_index=self.uv_index,
            air_quality=self.air_quality,
        )


class StyleRequestPayload(ApiModel):
    occasion: Optional[str] = None
    mood_tags: list[str] = Field(default_factory=list, alias="moodTags")
    formality: Optional[Formality] = None
    comfort_priority: str = Field(default="medium", alias="comfortPriority")
    preferred_colors: list[str] = Field(default_factory=list, alias="preferredColors")
    excluded_colors: list[str] = Field(default_factory=list, alias="excludedColors")
    avoid_tags: list[str] = Field(default_factory=list, alias="avoidTags")
    fixed_item_ids: list[str] = Field(default_factory=list, alias="fixedItemIds")
    excluded_item_ids: list[str] = Field(default_factory=list, alias="excludedItemIds")
    trend_level: TrendLevel = Field(default=TrendLevel.BALANCED, alias="trendLevel")

    def to_domain(self) -> StyleRequest:
        return StyleRequest(
            occasion=self.occasion,
            mood_tags=tuple(self.mood_tags),
            formality=self.formality,
            comfort_priority=self.comfort_priority,
            preferred_colors=tuple(self.preferred_colors),
            excluded_colors=tuple(self.excluded_colors),
            avoid_tags=tuple(self.avoid_tags),
            fixed_item_ids=tuple(self.fixed_item_ids),
            excluded_item_ids=tuple(self.excluded_item_ids),
            trend_level=self.trend_level,
        )


class TrendSignalPayload(ApiModel):
    tag: str
    strength: Annotated[float, Field(ge=0, le=1)]
    region: Optional[str] = None
    season: Optional[Season] = None

    def to_domain(self) -> TrendSignal:
        return TrendSignal(
            tag=self.tag,
            strength=self.strength,
            region=self.region,
            season=self.season,
        )


class RecommendationRequest(ApiModel):
    items: list[ClosetItemPayload] = Field(default_factory=list)
    weather: WeatherPayload
    style_request: StyleRequestPayload = Field(default_factory=StyleRequestPayload, alias="styleRequest")
    trends: list[TrendSignalPayload] = Field(default_factory=list)
    limit: Annotated[int, Field(ge=1, le=10)] = 3
    use_demo_closet: bool = Field(default=False, alias="useDemoCloset")

    @staticmethod
    def demo_style_request() -> StyleRequest:
        return StyleRequest(
            occasion="work",
            mood_tags=("minimal", "classic"),
            formality=Formality.BUSINESS_CASUAL,
            trend_level=TrendLevel.BALANCED,
        )


class OutfitItemResponse(ApiModel):
    id: str
    name: str
    category: Category
    sub_type: str = Field(alias="subType")
    colors: list[str]
    style_tags: list[str] = Field(alias="styleTags")


class OutfitCandidateResponse(ApiModel):
    item_ids: list[str] = Field(alias="itemIds")
    score: float
    reasons: list[str]
    items: list[OutfitItemResponse]


class RecommendationResponse(ApiModel):
    candidates: list[OutfitCandidateResponse]

    @classmethod
    def from_candidates(cls, candidates: list[OutfitCandidate]) -> "RecommendationResponse":
        return cls(candidates=[to_candidate_response(candidate) for candidate in candidates])


def to_candidate_response(candidate: OutfitCandidate) -> OutfitCandidateResponse:
    return OutfitCandidateResponse(
        itemIds=list(candidate.item_ids),
        score=candidate.score,
        reasons=list(candidate.reasons),
        items=[
            OutfitItemResponse(
                id=item.id,
                name=item.name,
                category=item.category,
                subType=item.sub_type,
                colors=list(item.colors),
                styleTags=list(item.style_tags),
            )
            for item in candidate.items
        ],
    )
