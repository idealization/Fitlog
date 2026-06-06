import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


class ApiFoundationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_health_returns_service_metadata(self):
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["service"], "Fitlog")
        self.assertEqual(body["status"], "ok")

    def test_demo_recommendations_return_candidates(self):
        response = self.client.get("/api/v1/recommendations/demo")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(len(body["candidates"]), 1)
        self.assertIn("itemIds", body["candidates"][0])
        self.assertIn("reasons", body["candidates"][0])

    def test_post_recommendations_accepts_inline_closet_payload(self):
        response = self.client.post(
            "/api/v1/recommendations",
            json={
                "items": [
                    {
                        "id": "shirt",
                        "name": "White shirt",
                        "category": "top",
                        "subType": "shirt",
                        "seasons": ["all"],
                        "styleTags": ["minimal"],
                        "colors": ["white"],
                        "formality": "business_casual",
                    },
                    {
                        "id": "slacks",
                        "name": "Black slacks",
                        "category": "bottom",
                        "subType": "slacks",
                        "seasons": ["all"],
                        "styleTags": ["minimal"],
                        "colors": ["black"],
                        "formality": "business_casual",
                    },
                    {
                        "id": "loafers",
                        "name": "Black loafers",
                        "category": "shoes",
                        "subType": "loafers",
                        "seasons": ["all"],
                        "styleTags": ["classic"],
                        "colors": ["black"],
                        "formality": "business_casual",
                    },
                ],
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

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(len(body["candidates"]), 1)
        self.assertIn("shirt", body["candidates"][0]["itemIds"])


if __name__ == "__main__":
    unittest.main()

