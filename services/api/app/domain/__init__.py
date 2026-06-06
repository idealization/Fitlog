"""Domain models and services for Fitlog."""

from .enums import (
    Category,
    Formality,
    ImageAnalysisJobStatus,
    ItemStatus,
    PrecipitationType,
    Season,
    Thickness,
    TrendLevel,
)
from .image_analysis import ImageAnalysisJob, ImageUploadTicket, WorkerEvent
from .models import ClosetItem, OutfitCandidate, StyleRequest, TrendSignal, WeatherSnapshot
from .recommendation import generate_outfit_recommendations

__all__ = [
    "Category",
    "ClosetItem",
    "Formality",
    "ImageAnalysisJob",
    "ImageAnalysisJobStatus",
    "ImageUploadTicket",
    "ItemStatus",
    "OutfitCandidate",
    "PrecipitationType",
    "Season",
    "StyleRequest",
    "Thickness",
    "TrendLevel",
    "TrendSignal",
    "WeatherSnapshot",
    "WorkerEvent",
    "generate_outfit_recommendations",
]
