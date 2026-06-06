from __future__ import annotations

from ..domain import (
    Category,
    ClosetItem,
    Formality,
    PrecipitationType,
    Season,
    Thickness,
    TrendSignal,
    WeatherSnapshot,
)


def demo_weather() -> WeatherSnapshot:
    return WeatherSnapshot(
        temperature_c=12,
        feels_like_c=10,
        precipitation_probability=0.2,
        precipitation_type=PrecipitationType.NONE,
        humidity=0.45,
        wind_speed_mps=2.0,
    )


def demo_trend_signals() -> list[TrendSignal]:
    return [
        TrendSignal(tag="minimal", strength=0.8, region="KR", season=Season.SPRING),
        TrendSignal(tag="classic", strength=0.6, region="KR", season=Season.SPRING),
    ]


def demo_closet_items() -> list[ClosetItem]:
    return [
        ClosetItem(
            id="demo-white-shirt",
            name="White oxford shirt",
            category=Category.TOP,
            sub_type="shirt",
            seasons=(Season.ALL,),
            style_tags=("minimal", "classic"),
            colors=("white",),
            formality=Formality.BUSINESS_CASUAL,
            thickness=Thickness.MEDIUM,
            warmth=4,
            breathability=7,
            last_worn_days_ago=7,
        ),
        ClosetItem(
            id="demo-black-slacks",
            name="Black slacks",
            category=Category.BOTTOM,
            sub_type="slacks",
            seasons=(Season.ALL,),
            style_tags=("minimal", "classic"),
            colors=("black",),
            formality=Formality.BUSINESS_CASUAL,
            thickness=Thickness.MEDIUM,
            warmth=5,
            breathability=5,
            last_worn_days_ago=10,
        ),
        ClosetItem(
            id="demo-loafers",
            name="Black loafers",
            category=Category.SHOES,
            sub_type="loafers",
            seasons=(Season.ALL,),
            style_tags=("classic",),
            colors=("black",),
            formality=Formality.BUSINESS_CASUAL,
            warmth=4,
            breathability=5,
            rain_safe=False,
            last_worn_days_ago=4,
        ),
        ClosetItem(
            id="demo-navy-jacket",
            name="Navy jacket",
            category=Category.OUTERWEAR,
            sub_type="jacket",
            seasons=(Season.SPRING, Season.FALL),
            style_tags=("minimal", "classic"),
            colors=("navy",),
            formality=Formality.BUSINESS_CASUAL,
            thickness=Thickness.MEDIUM,
            warmth=7,
            breathability=4,
            last_worn_days_ago=15,
        ),
    ]

