"""Domain models and services for Fitlog."""

from .enums import (
    Category,
    Formality,
    ImageAnalysisJobStatus,
    ItemStatus,
    PrecipitationType,
    RecommendationStatus,
    Season,
    Thickness,
    TrendLevel,
)
from .image_analysis import ImageAnalysisJob, ImageUploadTicket, WorkerEvent
from .models import ClosetItem, OutfitCandidate, StyleRequest, TrendSignal, WeatherSnapshot
from .recommendations import RecommendationFeedback, StoredOutfitCandidate, StoredRecommendation, WearLog
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
    "RecommendationFeedback",
    "RecommendationStatus",
    "Season",
    "StyleRequest",
    "StoredOutfitCandidate",
    "StoredRecommendation",
    "Thickness",
    "TrendLevel",
    "TrendSignal",
    "WeatherSnapshot",
    "WearLog",
    "WorkerEvent",
    "generate_outfit_recommendations",
]
