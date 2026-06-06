import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


def closet_item_payload(item_id="shirt"):
    return {
        "id": item_id,
        "name": "White oxford shirt",
        "category": "top",
        "subType": "shirt",
        "seasons": ["all"],
        "styleTags": ["minimal", "classic"],
        "colors": ["white"],
        "thickness": "medium",
        "formality": "business_casual",
        "status": "available",
        "warmth": 4,
        "rainSafe": False,
        "breathability": 7,
        "wearCount": 1,
        "lastWornDaysAgo": 7,
    }


class ClosetItemsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_create_list_get_patch_and_delete_closet_item(self):
        create_response = self.client.post("/api/v1/closet-items", json=closet_item_payload())

        self.assertEqual(create_response.status_code, 201)
        created = create_response.json()
        self.assertEqual(created["id"], "shirt")
        self.assertEqual(created["subType"], "shirt")

        list_response = self.client.get("/api/v1/closet-items")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        get_response = self.client.get("/api/v1/closet-items/shirt")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["name"], "White oxford shirt")

        patch_response = self.client.patch(
            "/api/v1/closet-items/shirt",
            json={"status": "laundry", "styleTags": ["minimal"]},
        )
        self.assertEqual(patch_response.status_code, 200)
        patched = patch_response.json()
        self.assertEqual(patched["status"], "laundry")
        self.assertEqual(patched["styleTags"], ["minimal"])

        delete_response = self.client.delete("/api/v1/closet-items/shirt")
        self.assertEqual(delete_response.status_code, 204)

        missing_response = self.client.get("/api/v1/closet-items/shirt")
        self.assertEqual(missing_response.status_code, 404)

    def test_duplicate_create_returns_conflict(self):
        first_response = self.client.post("/api/v1/closet-items", json=closet_item_payload())
        second_response = self.client.post("/api/v1/closet-items", json=closet_item_payload())

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 409)

    def test_recommendation_uses_stored_closet_when_inline_items_are_absent(self):
        items = [
            closet_item_payload("shirt"),
            {
                **closet_item_payload("slacks"),
                "name": "Black slacks",
                "category": "bottom",
                "subType": "slacks",
                "colors": ["black"],
            },
            {
                **closet_item_payload("loafers"),
                "name": "Black loafers",
                "category": "shoes",
                "subType": "loafers",
                "colors": ["black"],
            },
        ]
        for item in items:
            response = self.client.post("/api/v1/closet-items", json=item)
            self.assertEqual(response.status_code, 201)

        recommendation_response = self.client.post(
            "/api/v1/recommendations",
            json={
                "weather": {
                    "temperatureC": 20,
                    "feelsLikeC": 20,
                    "precipitationProbability": 0.1,
                    "precipitationType": "none",
                },
                "styleRequest": {
                    "occasion": "work",
                    "moodTags": ["minimal"],
                    "formality": "business_casual",
                },
                "trends": [{"tag": "minimal", "strength": 0.8}],
            },
        )

        self.assertEqual(recommendation_response.status_code, 200)
        candidates = recommendation_response.json()["candidates"]
        self.assertGreaterEqual(len(candidates), 1)
        self.assertIn("shirt", candidates[0]["itemIds"])
        self.assertIn("slacks", candidates[0]["itemIds"])
        self.assertIn("loafers", candidates[0]["itemIds"])


if __name__ == "__main__":
    unittest.main()

