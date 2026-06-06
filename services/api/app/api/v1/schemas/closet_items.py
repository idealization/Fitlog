from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field

from ....domain import Category, ClosetItem, Formality, ItemStatus, Season, Thickness


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, use_enum_values=False)


class ClosetItemCreateRequest(ApiModel):
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


class ClosetItemUpdateRequest(ApiModel):
    name: Optional[str] = None
    category: Optional[Category] = None
    sub_type: Optional[str] = Field(default=None, alias="subType")
    seasons: Optional[list[Season]] = None
    style_tags: Optional[list[str]] = Field(default=None, alias="styleTags")
    colors: Optional[list[str]] = None
    thickness: Optional[Thickness] = None
    formality: Optional[Formality] = None
    status: Optional[ItemStatus] = None
    warmth: Annotated[Optional[int], Field(ge=0, le=10)] = None
    rain_safe: Optional[bool] = Field(default=None, alias="rainSafe")
    breathability: Annotated[Optional[int], Field(ge=0, le=10)] = None
    wear_count: Annotated[Optional[int], Field(ge=0)] = Field(default=None, alias="wearCount")
    last_worn_days_ago: Annotated[Optional[int], Field(ge=0)] = Field(default=None, alias="lastWornDaysAgo")

    def to_changes(self) -> dict[str, object]:
        changes: dict[str, object] = {}
        fields = self.model_fields_set

        for field_name in (
            "name",
            "category",
            "sub_type",
            "thickness",
            "formality",
            "status",
            "warmth",
            "rain_safe",
            "breathability",
            "wear_count",
            "last_worn_days_ago",
        ):
            if field_name in fields:
                value = getattr(self, field_name)
                if value is not None or field_name == "last_worn_days_ago":
                    changes[field_name] = value

        if "seasons" in fields and self.seasons is not None:
            changes["seasons"] = tuple(self.seasons)
        if "style_tags" in fields and self.style_tags is not None:
            changes["style_tags"] = tuple(self.style_tags)
        if "colors" in fields and self.colors is not None:
            changes["colors"] = tuple(self.colors)

        return changes


class ClosetItemResponse(ApiModel):
    id: str
    name: str
    category: Category
    sub_type: str = Field(alias="subType")
    seasons: list[Season]
    style_tags: list[str] = Field(alias="styleTags")
    colors: list[str]
    thickness: Thickness
    formality: Formality
    status: ItemStatus
    warmth: int
    rain_safe: bool = Field(alias="rainSafe")
    breathability: int
    wear_count: int = Field(alias="wearCount")
    last_worn_days_ago: Optional[int] = Field(alias="lastWornDaysAgo")


def to_closet_item_response(item: ClosetItem) -> ClosetItemResponse:
    return ClosetItemResponse(
        id=item.id,
        name=item.name,
        category=item.category,
        subType=item.sub_type,
        seasons=list(item.seasons),
        styleTags=list(item.style_tags),
        colors=list(item.colors),
        thickness=item.thickness,
        formality=item.formality,
        status=item.status,
        warmth=item.warmth,
        rainSafe=item.rain_safe,
        breathability=item.breathability,
        wearCount=item.wear_count,
        lastWornDaysAgo=item.last_worn_days_ago,
    )

