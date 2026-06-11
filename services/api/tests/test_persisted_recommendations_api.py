import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


def sqlite_settings(path: Path) -> Settings:
    return Settings(
        environment="test",
        repository_backend="sqlite",
        database_url=f"sqlite:///{path}",
    )


def recommendation_payload():
    return {
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
    }


class PersistedRecommendationsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_create_get_save_wear_and_feedback(self):
        create_response = self.client.post("/api/v1/recommendations", json=recommendation_payload())

        self.assertEqual(create_response.status_code, 200)
        created = create_response.json()
        recommendation_id = created["recommendationId"]
        self.assertEqual(created["status"], "candidate")
        self.assertGreaterEqual(len(created["candidates"]), 1)

        get_response = self.client.get(f"/api/v1/recommendations/{recommendation_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["recommendationId"], recommendation_id)

        save_response = self.client.post(f"/api/v1/recommendations/{recommendation_id}/save")
        self.assertEqual(save_response.status_code, 200)
        self.assertEqual(save_response.json()["status"], "saved")

        feedback_response = self.client.post(
            f"/api/v1/recommendations/{recommendation_id}/feedback",
            json={"feedbackType": "liked", "note": "Good for work"},
        )
        self.assertEqual(feedback_response.status_code, 200)
        self.assertEqual(feedback_response.json()["feedbackType"], "liked")

        wear_response = self.client.post(f"/api/v1/recommendations/{recommendation_id}/wear")
        self.assertEqual(wear_response.status_code, 200)
        self.assertIn("shirt", wear_response.json()["itemIds"])

        worn_response = self.client.get(f"/api/v1/recommendations/{recommendation_id}")
        self.assertEqual(worn_response.status_code, 200)
        self.assertEqual(worn_response.json()["status"], "worn")

    def test_missing_recommendation_actions_return_404(self):
        self.assertEqual(self.client.get("/api/v1/recommendations/missing").status_code, 404)
        self.assertEqual(self.client.post("/api/v1/recommendations/missing/save").status_code, 404)
        self.assertEqual(self.client.post("/api/v1/recommendations/missing/wear").status_code, 404)
        self.assertEqual(
            self.client.post(
                "/api/v1/recommendations/missing/feedback",
                json={"feedbackType": "liked"},
            ).status_code,
            404,
        )

    def test_sqlite_recommendation_feedback_and_wear_log_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "fitlog-recommendations.db"
            first_client = TestClient(create_app(sqlite_settings(database_path)))

            create_response = first_client.post("/api/v1/recommendations", json=recommendation_payload())
            self.assertEqual(create_response.status_code, 200)
            recommendation_id = create_response.json()["recommendationId"]

            self.assertEqual(first_client.post(f"/api/v1/recommendations/{recommendation_id}/save").status_code, 200)
            self.assertEqual(
                first_client.post(
                    f"/api/v1/recommendations/{recommendation_id}/feedback",
                    json={"feedbackType": "too_hot"},
                ).status_code,
                200,
            )
            self.assertEqual(first_client.post(f"/api/v1/recommendations/{recommendation_id}/wear").status_code, 200)

            second_client = TestClient(create_app(sqlite_settings(database_path)))
            get_response = second_client.get(f"/api/v1/recommendations/{recommendation_id}")

            self.assertEqual(get_response.status_code, 200)
            self.assertEqual(get_response.json()["status"], "worn")

            with sqlite3.connect(database_path) as connection:
                feedback_count = connection.execute("select count(*) from recommendation_feedback").fetchone()[0]
                wear_log_count = connection.execute("select count(*) from wear_logs").fetchone()[0]

            self.assertEqual(feedback_count, 1)
            self.assertEqual(wear_log_count, 1)


if __name__ == "__main__":
    unittest.main()

