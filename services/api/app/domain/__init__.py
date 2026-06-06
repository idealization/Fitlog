"""Domain models and services for Fitlog."""

from .enums import Category, Formality, ItemStatus, PrecipitationType, Season, Thickness, TrendLevel
from .models import ClosetItem, OutfitCandidate, StyleRequest, TrendSignal, WeatherSnapshot
from .recommendation import generate_outfit_recommendations

__all__ = [
    "Category",
    "ClosetItem",
    "Formality",
    "ItemStatus",
    "OutfitCandidate",
    "PrecipitationType",
    "Season",
    "StyleRequest",
    "Thickness",
    "TrendLevel",
    "TrendSignal",
    "WeatherSnapshot",
    "generate_outfit_recommendations",
]

