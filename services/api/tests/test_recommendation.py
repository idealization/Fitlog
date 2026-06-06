import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.domain import (  # noqa: E402
    Category,
    ClosetItem,
    Formality,
    ItemStatus,
    PrecipitationType,
    Season,
    StyleRequest,
    Thickness,
    TrendLevel,
    TrendSignal,
    WeatherSnapshot,
    generate_outfit_recommendations,
)


class RecommendationTests(unittest.TestCase):
    def test_cold_rainy_work_recommendation_uses_outerwear_and_rain_safe_shoes(self):
        items = [
            ClosetItem(
                id="shirt",
                name="White shirt",
                category=Category.TOP,
                sub_type="shirt",
                seasons=(Season.ALL,),
                style_tags=("minimal", "classic"),
                colors=("white",),
                formality=Formality.BUSINESS_CASUAL,
                warmth=4,
                breathability=6,
            ),
            ClosetItem(
                id="slacks",
                name="Black slacks",
                category=Category.BOTTOM,
                sub_type="slacks",
                seasons=(Season.ALL,),
                style_tags=("minimal", "classic"),
                colors=("black",),
                formality=Formality.BUSINESS_CASUAL,
                warmth=5,
            ),
            ClosetItem(
                id="boots",
                name="Rain boots",
                category=Category.SHOES,
                sub_type="boots",
                seasons=(Season.FALL, Season.WINTER),
                style_tags=("minimal",),
                colors=("black",),
                formality=Formality.BUSINESS_CASUAL,
                rain_safe=True,
                warmth=5,
            ),
            ClosetItem(
                id="sneakers",
                name="Canvas sneakers",
                category=Category.SHOES,
                sub_type="sneakers",
                seasons=(Season.ALL,),
                style_tags=("casual",),
                colors=("white",),
                status=ItemStatus.LAUNDRY,
            ),
            ClosetItem(
                id="coat",
                name="Wool coat",
                category=Category.OUTERWEAR,
                sub_type="coat",
                seasons=(Season.FALL, Season.WINTER),
                style_tags=("classic",),
                colors=("navy",),
                formality=Formality.BUSINESS_CASUAL,
                thickness=Thickness.HEAVY,
                warmth=9,
            ),
        ]
        weather = WeatherSnapshot(
            temperature_c=7,
            feels_like_c=5,
            precipitation_probability=0.8,
            precipitation_type=PrecipitationType.RAIN,
        )
        request = StyleRequest(occasion="work", mood_tags=("minimal",), formality=Formality.BUSINESS_CASUAL)

        recommendations = generate_outfit_recommendations(items, weather, request)

        self.assertGreaterEqual(len(recommendations), 1)
        top = recommendations[0]
        self.assertIn("coat", top.item_ids)
        self.assertIn("boots", top.item_ids)
        self.assertNotIn("sneakers", top.item_ids)
        self.assertTrue(any("비 예보" in reason for reason in top.reasons))

    def test_hot_weather_filters_heavy_non_shoe_items(self):
        items = [
            ClosetItem(
                id="heavy-knit",
                name="Heavy knit",
                category=Category.TOP,
                sub_type="knit",
                seasons=(Season.WINTER,),
                style_tags=("classic",),
                colors=("cream",),
                thickness=Thickness.HEAVY,
                warmth=8,
                breathability=2,
            ),
            ClosetItem(
                id="linen-shirt",
                name="Linen shirt",
                category=Category.TOP,
                sub_type="shirt",
                seasons=(Season.SUMMER,),
                style_tags=("minimal",),
                colors=("white",),
                thickness=Thickness.LIGHT,
                warmth=2,
                breathability=9,
            ),
            ClosetItem(
                id="shorts",
                name="Navy shorts",
                category=Category.BOTTOM,
                sub_type="shorts",
                seasons=(Season.SUMMER,),
                style_tags=("minimal",),
                colors=("navy",),
                thickness=Thickness.LIGHT,
                breathability=8,
            ),
            ClosetItem(
                id="sandals",
                name="Sandals",
                category=Category.SHOES,
                sub_type="sandals",
                seasons=(Season.SUMMER,),
                style_tags=("casual",),
                colors=("brown",),
                breathability=9,
            ),
        ]
        weather = WeatherSnapshot(temperature_c=31, feels_like_c=33, precipitation_probability=0.1)
        request = StyleRequest(mood_tags=("minimal",), trend_level=TrendLevel.BASIC)

        recommendations = generate_outfit_recommendations(items, weather, request)

        self.assertGreaterEqual(len(recommendations), 1)
        self.assertNotIn("heavy-knit", recommendations[0].item_ids)
        self.assertIn("linen-shirt", recommendations[0].item_ids)
        self.assertTrue(any("더운 날씨" in reason for reason in recommendations[0].reasons))

    def test_fixed_and_excluded_items_are_respected(self):
        items = [
            ClosetItem(
                id="tee",
                name="White tee",
                category=Category.TOP,
                sub_type="t-shirt",
                seasons=(Season.ALL,),
                style_tags=("casual",),
                colors=("white",),
            ),
            ClosetItem(
                id="denim",
                name="Blue denim",
                category=Category.BOTTOM,
                sub_type="denim",
                seasons=(Season.ALL,),
                style_tags=("casual",),
                colors=("denim",),
            ),
            ClosetItem(
                id="slacks",
                name="Black slacks",
                category=Category.BOTTOM,
                sub_type="slacks",
                seasons=(Season.ALL,),
                style_tags=("minimal",),
                colors=("black",),
            ),
            ClosetItem(
                id="sneakers",
                name="Sneakers",
                category=Category.SHOES,
                sub_type="sneakers",
                seasons=(Season.ALL,),
                style_tags=("casual",),
                colors=("white",),
            ),
        ]
        weather = WeatherSnapshot(temperature_c=20, feels_like_c=20, precipitation_probability=0.0)
        request = StyleRequest(fixed_item_ids=("tee",), excluded_item_ids=("denim",))

        recommendations = generate_outfit_recommendations(items, weather, request)

        self.assertGreaterEqual(len(recommendations), 1)
        self.assertIn("tee", recommendations[0].item_ids)
        self.assertNotIn("denim", recommendations[0].item_ids)

    def test_trend_and_mood_tags_influence_ranking(self):
        items = [
            ClosetItem(
                id="minimal-shirt",
                name="Minimal shirt",
                category=Category.TOP,
                sub_type="shirt",
                seasons=(Season.ALL,),
                style_tags=("minimal", "classic"),
                colors=("white",),
                formality=Formality.BUSINESS_CASUAL,
            ),
            ClosetItem(
                id="graphic-tee",
                name="Graphic tee",
                category=Category.TOP,
                sub_type="t-shirt",
                seasons=(Season.ALL,),
                style_tags=("street",),
                colors=("red",),
                formality=Formality.CASUAL,
            ),
            ClosetItem(
                id="black-slacks",
                name="Black slacks",
                category=Category.BOTTOM,
                sub_type="slacks",
                seasons=(Season.ALL,),
                style_tags=("minimal",),
                colors=("black",),
                formality=Formality.BUSINESS_CASUAL,
            ),
            ClosetItem(
                id="black-shoes",
                name="Black shoes",
                category=Category.SHOES,
                sub_type="loafers",
                seasons=(Season.ALL,),
                style_tags=("classic",),
                colors=("black",),
                formality=Formality.BUSINESS_CASUAL,
            ),
        ]
        weather = WeatherSnapshot(temperature_c=19, feels_like_c=19, precipitation_probability=0.0)
        request = StyleRequest(
            occasion="work",
            mood_tags=("minimal",),
            formality=Formality.BUSINESS_CASUAL,
            trend_level=TrendLevel.BALANCED,
        )
        trends = [TrendSignal(tag="minimal", strength=0.8)]

        recommendations = generate_outfit_recommendations(items, weather, request, trends=trends)

        self.assertGreaterEqual(len(recommendations), 1)
        self.assertIn("minimal-shirt", recommendations[0].item_ids)
        self.assertNotIn("graphic-tee", recommendations[0].item_ids)
        self.assertTrue(any("minimal" in reason for reason in recommendations[0].reasons))


if __name__ == "__main__":
    unittest.main()

