from __future__ import annotations

from itertools import product

from .enums import Category, Formality, ItemStatus, PrecipitationType, Season, Thickness, TrendLevel
from .models import ClosetItem, OutfitCandidate, StyleRequest, TrendSignal, WeatherSnapshot

NEUTRAL_COLORS = {"black", "white", "gray", "grey", "navy", "beige", "cream", "brown", "denim"}


def generate_outfit_recommendations(
    items: list[ClosetItem],
    weather: WeatherSnapshot,
    request: StyleRequest,
    trends: list[TrendSignal] | None = None,
    limit: int = 3,
) -> list[OutfitCandidate]:
    """Generate deterministic outfit candidates from closet state and context."""
    trend_signals = trends or []
    eligible = [_item for _item in items if _is_eligible(_item, weather, request)]

    grouped = _group_by_category(eligible)
    candidates = _build_candidates(grouped, weather)

    fixed_ids = set(request.fixed_item_ids)
    if fixed_ids:
        candidates = [candidate for candidate in candidates if fixed_ids.issubset({item.id for item in candidate})]

    scored = [
        OutfitCandidate(
            items=tuple(candidate),
            score=round(_score_candidate(candidate, weather, request, trend_signals), 4),
            reasons=tuple(_build_reasons(candidate, weather, request, trend_signals)),
        )
        for candidate in candidates
    ]

    scored = [candidate for candidate in scored if candidate.score > 0]
    scored.sort(key=lambda candidate: (-candidate.score, candidate.item_ids))
    return scored[:limit]


def _is_eligible(item: ClosetItem, weather: WeatherSnapshot, request: StyleRequest) -> bool:
    if item.status is not ItemStatus.AVAILABLE:
        return False
    if item.id in request.excluded_item_ids:
        return False
    if set(item.colors) & set(request.excluded_colors):
        return False
    if set(item.style_tags) & set(request.avoid_tags):
        return False
    if _is_hot(weather) and item.thickness is Thickness.HEAVY and item.category is not Category.SHOES:
        return False
    if not _matches_season(item, weather):
        return False
    return True


def _matches_season(item: ClosetItem, weather: WeatherSnapshot) -> bool:
    if Season.ALL in item.seasons:
        return True

    target = _weather_season(weather)
    if target in item.seasons:
        return True

    if target is Season.WINTER and Season.FALL in item.seasons and item.category is not Category.TOP:
        return True
    if target is Season.SUMMER and Season.SPRING in item.seasons and item.thickness is Thickness.LIGHT:
        return True
    return False


def _weather_season(weather: WeatherSnapshot) -> Season:
    if weather.feels_like_c <= 8:
        return Season.WINTER
    if weather.feels_like_c >= 26:
        return Season.SUMMER
    if weather.feels_like_c >= 18:
        return Season.SPRING
    return Season.FALL


def _group_by_category(items: list[ClosetItem]) -> dict[Category, list[ClosetItem]]:
    grouped: dict[Category, list[ClosetItem]] = {category: [] for category in Category}
    for item in items:
        grouped[item.category].append(item)
    return grouped


def _build_candidates(grouped: dict[Category, list[ClosetItem]], weather: WeatherSnapshot) -> list[list[ClosetItem]]:
    candidates: list[list[ClosetItem]] = []
    tops = grouped[Category.TOP]
    bottoms = grouped[Category.BOTTOM]
    dresses = grouped[Category.DRESS]
    shoes = grouped[Category.SHOES]
    outerwear = grouped[Category.OUTERWEAR]

    needs_outerwear = _needs_outerwear(weather)
    outer_options: list[ClosetItem | None] = outerwear if needs_outerwear else [None, *outerwear]

    for top, bottom, shoe, outer in product(tops, bottoms, shoes, outer_options):
        candidate = [top, bottom, shoe]
        if outer is not None:
            candidate.append(outer)
        candidates.append(candidate)

    for dress, shoe, outer in product(dresses, shoes, outer_options):
        candidate = [dress, shoe]
        if outer is not None:
            candidate.append(outer)
        candidates.append(candidate)

    return candidates


def _score_candidate(
    candidate: list[ClosetItem],
    weather: WeatherSnapshot,
    request: StyleRequest,
    trends: list[TrendSignal],
) -> float:
    return (
        0.25 * _user_preference_match(candidate, request)
        + 0.20 * _weather_fit(candidate, weather)
        + 0.15 * _color_harmony(candidate, request)
        + 0.15 * _occasion_fit(candidate, request)
        + 0.10 * _trend_match(candidate, request, trends)
        + 0.10 * _freshness(candidate)
        + 0.05 * _closet_utilization(candidate)
    )


def _user_preference_match(candidate: list[ClosetItem], request: StyleRequest) -> float:
    if not request.mood_tags and not request.preferred_colors:
        return 0.7

    tags = _candidate_tags(candidate)
    colors = _candidate_colors(candidate)
    tag_score = _overlap_score(tags, set(request.mood_tags)) if request.mood_tags else 0.6
    color_score = _overlap_score(colors, set(request.preferred_colors)) if request.preferred_colors else 0.6
    return (tag_score + color_score) / 2


def _weather_fit(candidate: list[ClosetItem], weather: WeatherSnapshot) -> float:
    score = 0.65
    warmth = sum(item.warmth for item in candidate)
    breathable = sum(item.breathability for item in candidate) / max(len(candidate), 1)

    if _needs_outerwear(weather):
        has_outerwear = any(item.category is Category.OUTERWEAR for item in candidate)
        score += 0.2 if has_outerwear else -0.25
        score += min(warmth / 35, 0.2)

    if _is_hot(weather):
        score += 0.2 if breathable >= 7 else -0.15
        if any(item.thickness is Thickness.HEAVY for item in candidate):
            score -= 0.2

    if _is_rainy(weather):
        has_rain_safe_shoes = any(item.category is Category.SHOES and item.rain_safe for item in candidate)
        score += 0.2 if has_rain_safe_shoes else -0.25

    return _clamp(score)


def _color_harmony(candidate: list[ClosetItem], request: StyleRequest) -> float:
    colors = _candidate_colors(candidate)
    if not colors:
        return 0.5

    if request.preferred_colors and colors & set(request.preferred_colors):
        return 0.9

    neutral_count = len(colors & NEUTRAL_COLORS)
    if len(colors) <= 3 and neutral_count >= 1:
        return 0.85
    if len(colors) <= 2:
        return 0.8
    return 0.55


def _occasion_fit(candidate: list[ClosetItem], request: StyleRequest) -> float:
    target = request.formality
    if target is None:
        target = Formality.BUSINESS_CASUAL if request.occasion in {"work", "interview"} else Formality.CASUAL

    distances = [_formality_distance(item.formality, target) for item in candidate]
    average_distance = sum(distances) / max(len(distances), 1)
    return _clamp(1 - average_distance / 2)


def _trend_match(candidate: list[ClosetItem], request: StyleRequest, trends: list[TrendSignal]) -> float:
    if request.trend_level is TrendLevel.BASIC or not trends:
        return 0.5

    tags = _candidate_tags(candidate)
    matching_strength = sum(_clamp(signal.strength) for signal in trends if signal.tag in tags)
    intensity = 1.0 if request.trend_level is TrendLevel.EXPERIMENTAL else 0.7
    return _clamp(0.45 + matching_strength * 0.25 * intensity)


def _freshness(candidate: list[ClosetItem]) -> float:
    values: list[float] = []
    for item in candidate:
        if item.last_worn_days_ago is None:
            values.append(0.8)
        elif item.last_worn_days_ago >= 14:
            values.append(1.0)
        elif item.last_worn_days_ago >= 5:
            values.append(0.75)
        else:
            values.append(0.35)
    return sum(values) / max(len(values), 1)


def _closet_utilization(candidate: list[ClosetItem]) -> float:
    values = [1.0 if item.wear_count <= 2 else 0.6 if item.wear_count <= 8 else 0.35 for item in candidate]
    return sum(values) / max(len(values), 1)


def _build_reasons(
    candidate: list[ClosetItem],
    weather: WeatherSnapshot,
    request: StyleRequest,
    trends: list[TrendSignal],
) -> list[str]:
    reasons: list[str] = []

    if _is_rainy(weather) and any(item.category is Category.SHOES and item.rain_safe for item in candidate):
        reasons.append("비 예보를 고려해 젖어도 부담이 적은 신발을 우선했어요.")
    elif _needs_outerwear(weather) and any(item.category is Category.OUTERWEAR for item in candidate):
        reasons.append("체감온도가 낮아 아우터를 포함했어요.")
    elif _is_hot(weather):
        reasons.append("더운 날씨에 맞춰 가볍고 통기성 있는 조합을 골랐어요.")

    matching_moods = sorted(_candidate_tags(candidate) & set(request.mood_tags))
    if matching_moods:
        reasons.append(f"요청한 분위기와 맞는 태그를 반영했어요: {', '.join(matching_moods[:2])}.")

    matching_trends = sorted(_candidate_tags(candidate) & {signal.tag for signal in trends})
    if request.trend_level is not TrendLevel.BASIC and matching_trends:
        reasons.append(f"최근 트렌드 태그를 자연스럽게 섞었어요: {', '.join(matching_trends[:2])}.")

    if not reasons:
        reasons.append("색상과 상황 적합도가 안정적인 조합이에요.")

    return reasons[:3]


def _candidate_tags(candidate: list[ClosetItem]) -> set[str]:
    return {tag for item in candidate for tag in item.style_tags}


def _candidate_colors(candidate: list[ClosetItem]) -> set[str]:
    return {color for item in candidate for color in item.colors}


def _overlap_score(values: set[str], targets: set[str]) -> float:
    if not targets:
        return 0.6
    return _clamp(len(values & targets) / len(targets))


def _formality_distance(actual: Formality, target: Formality) -> int:
    order = {
        Formality.CASUAL: 0,
        Formality.BUSINESS_CASUAL: 1,
        Formality.FORMAL: 2,
    }
    return abs(order[actual] - order[target])


def _needs_outerwear(weather: WeatherSnapshot) -> bool:
    return weather.feels_like_c < 13


def _is_hot(weather: WeatherSnapshot) -> bool:
    return weather.feels_like_c >= 27


def _is_rainy(weather: WeatherSnapshot) -> bool:
    return (
        weather.precipitation_type in {PrecipitationType.RAIN, PrecipitationType.SNOW}
        or weather.precipitation_probability >= 0.5
    )


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(value, upper))

