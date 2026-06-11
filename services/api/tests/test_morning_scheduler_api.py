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


def closet_item_payload(item_id="shirt", category="top", sub_type="shirt", colors=None):
    return {
        "id": item_id,
        "name": item_id.replace("-", " ").title(),
        "category": category,
        "subType": sub_type,
        "seasons": ["all"],
        "styleTags": ["minimal"],
        "colors": colors or ["white"],
        "formality": "business_casual",
        "warmth": 4,
        "breathability": 7,
    }


def seed_minimal_closet(client: TestClient):
    items = [
        closet_item_payload("shirt", "top", "shirt", ["white"]),
        closet_item_payload("slacks", "bottom", "slacks", ["black"]),
        closet_item_payload("loafers", "shoes", "loafers", ["black"]),
    ]
    for item in items:
        response = client.post("/api/v1/closet-items", json=item)
        assert response.status_code == 201


class MorningSchedulerApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_notification_settings_can_be_read_and_updated(self):
        default_response = self.client.get("/api/v1/notification-settings")
        self.assertEqual(default_response.status_code, 200)
        self.assertFalse(default_response.json()["enabled"])

        update_response = self.client.patch(
            "/api/v1/notification-settings",
            json={
                "enabled": True,
                "timezone": "UTC",
                "weekdayNotificationTime": "08:00",
                "weekendNotificationTime": "09:30",
                "locationLabel": "Seoul",
                "latitude": 37.5665,
                "longitude": 126.978,
            },
        )

        self.assertEqual(update_response.status_code, 200)
        body = update_response.json()
        self.assertTrue(body["enabled"])
        self.assertEqual(body["timezone"], "UTC")
        self.assertEqual(body["weekdayNotificationTime"], "08:00")
        self.assertEqual(body["weekendNotificationTime"], "09:30")

    def test_run_due_creates_recommendation_and_placeholder_push_once_per_day(self):
        seed_minimal_closet(self.client)
        self.client.patch(
            "/api/v1/notification-settings",
            json={"enabled": True, "timezone": "UTC", "weekdayNotificationTime": "08:00"},
        )

        before_due = self.client.post(
            "/api/v1/morning-recommendations/run-due",
            json={"now": "2026-06-11T07:59:00+00:00"},
        )
        self.assertEqual(before_due.status_code, 200)
        self.assertFalse(before_due.json()["created"])
        self.assertEqual(before_due.json()["reason"], "not_due")

        due_response = self.client.post(
            "/api/v1/morning-recommendations/run-due",
            json={
                "now": "2026-06-11T08:00:00+00:00",
                "weather": {
                    "temperatureC": 21,
                    "feelsLikeC": 21,
                    "precipitationProbability": 0.1,
                    "precipitationType": "none",
                },
            },
        )

        self.assertEqual(due_response.status_code, 200)
        due_body = due_response.json()
        self.assertTrue(due_body["created"])
        self.assertEqual(due_body["reason"], "created")
        self.assertEqual(due_body["weatherSource"], "provided")
        self.assertIsNotNone(due_body["recommendationId"])
        self.assertEqual(due_body["pushDispatch"]["status"], "queued")

        recommendation_response = self.client.get(f"/api/v1/recommendations/{due_body['recommendationId']}")
        self.assertEqual(recommendation_response.status_code, 200)
        self.assertEqual(recommendation_response.json()["recommendationId"], due_body["recommendationId"])

        second_run = self.client.post(
            "/api/v1/morning-recommendations/run-due",
            json={"now": "2026-06-11T08:10:00+00:00"},
        )
        self.assertEqual(second_run.status_code, 200)
        self.assertFalse(second_run.json()["created"])
        self.assertEqual(second_run.json()["reason"], "already_created")
        self.assertEqual(second_run.json()["recommendationId"], due_body["recommendationId"])

    def test_disabled_notification_settings_skip_scheduler(self):
        response = self.client.post(
            "/api/v1/morning-recommendations/run-due",
            json={"now": "2026-06-11T09:00:00+00:00"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["created"])
        self.assertEqual(response.json()["reason"], "disabled")

    def test_sqlite_scheduler_state_persists_across_app_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "fitlog-scheduler.db"
            first_client = TestClient(create_app(sqlite_settings(database_path)))
            seed_minimal_closet(first_client)
            first_client.patch(
                "/api/v1/notification-settings",
                json={"enabled": True, "timezone": "UTC", "weekdayNotificationTime": "08:00"},
            )

            run_response = first_client.post(
                "/api/v1/morning-recommendations/run-due",
                json={"now": "2026-06-11T08:00:00+00:00"},
            )
            self.assertEqual(run_response.status_code, 200)
            self.assertTrue(run_response.json()["created"])

            second_client = TestClient(create_app(sqlite_settings(database_path)))
            second_run = second_client.post(
                "/api/v1/morning-recommendations/run-due",
                json={"now": "2026-06-11T08:30:00+00:00"},
            )
            self.assertEqual(second_run.status_code, 200)
            self.assertFalse(second_run.json()["created"])
            self.assertEqual(second_run.json()["reason"], "already_created")

            with sqlite3.connect(database_path) as connection:
                run_count = connection.execute("select count(*) from morning_recommendation_runs").fetchone()[0]
                dispatch_count = connection.execute("select count(*) from push_dispatches").fetchone()[0]

            self.assertEqual(run_count, 1)
            self.assertEqual(dispatch_count, 1)


if __name__ == "__main__":
    unittest.main()

