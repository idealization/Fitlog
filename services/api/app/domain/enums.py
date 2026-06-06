from enum import Enum


class Category(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    OUTERWEAR = "outerwear"
    DRESS = "dress"
    SHOES = "shoes"
    BAG = "bag"
    ACCESSORY = "accessory"


class ItemStatus(str, Enum):
    AVAILABLE = "available"
    LAUNDRY = "laundry"
    REPAIR = "repair"
    STORAGE = "storage"
    SELL_OR_DONATE = "sell_or_donate"


class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    ALL = "all"


class Thickness(str, Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


class Formality(str, Enum):
    CASUAL = "casual"
    BUSINESS_CASUAL = "business_casual"
    FORMAL = "formal"


class PrecipitationType(str, Enum):
    NONE = "none"
    RAIN = "rain"
    SNOW = "snow"


class TrendLevel(str, Enum):
    BASIC = "basic"
    BALANCED = "balanced"
    EXPERIMENTAL = "experimental"

