"""Tests for ops dashboard health + catalog save API."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from berichtsheft import catalog, db
from berichtsheft.api_server import app


class TestDashboard(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        # Empty token = open access in tests (setdefault in load_dotenv won't override)
        os.environ["DASHBOARD_TOKEN"] = ""

    def tearDown(self) -> None:
        os.environ["DASHBOARD_TOKEN"] = ""

    def test_health_json(self) -> None:
        r = self.client.get("/dashboard/api/health")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["api"])
        self.assertIn("gemini_enabled", data)
        self.assertIn("vision_enabled", data)
        self.assertIn("telegram_token_present", data)
        self.assertIn("whatsapp_allowlist_set", data)
        self.assertIn("waha", data)
        self.assertIn("auth_note", data)

    def test_dashboard_html(self) -> None:
        r = self.client.get("/dashboard")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Berichtsheft", r.text)
        self.assertIn("Ops Console", r.text)

    def test_catalog_save_endpoint(self) -> None:
        original = catalog.load_katalog()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            katalog_path = tmp_path / "katalog_abteilung.json"
            db_path = tmp_path / "test.db"
            katalog_path.write_text(
                json.dumps(original, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # Mutate a known field
            mutated = json.loads(json.dumps(original))
            mutated["note"] = "dashboard-test-note"

            with mock.patch.object(catalog, "KATALOG_PATH", katalog_path), mock.patch.object(
                catalog, "AREAS_PATH", tmp_path / "areas_hotel.json"
            ), mock.patch.object(
                catalog, "TEMPLATES_PATH", tmp_path / "templates_hotelfach.json"
            ), mock.patch.object(db, "DEFAULT_DB", db_path), mock.patch(
                "berichtsheft.dashboard.db.DEFAULT_DB", db_path
            ), mock.patch(
                "berichtsheft.dashboard.catalog.KATALOG_PATH", katalog_path
            ), mock.patch(
                "berichtsheft.dashboard.catalog.AREAS_PATH", tmp_path / "areas_hotel.json"
            ), mock.patch(
                "berichtsheft.dashboard.catalog.TEMPLATES_PATH",
                tmp_path / "templates_hotelfach.json",
            ):
                r = self.client.put(
                    "/dashboard/api/catalog",
                    json={
                        "katalog": mutated,
                        "sync_db": True,
                        "export_legacy": True,
                        "write_md": False,
                    },
                )
                self.assertEqual(r.status_code, 200, r.text)
                body = r.json()
                self.assertTrue(body["ok"])
                self.assertIsNotNone(body.get("sync"))
                self.assertGreater(body["sync"]["templates"], 0)

                saved = json.loads(katalog_path.read_text(encoding="utf-8"))
                self.assertEqual(saved["note"], "dashboard-test-note")

                conn = db.connect(db_path)
                n = conn.execute(
                    "SELECT COUNT(*) AS n FROM activity_templates"
                ).fetchone()["n"]
                conn.close()
                self.assertGreater(n, 0)

    def test_token_required_when_set(self) -> None:
        os.environ["DASHBOARD_TOKEN"] = "secret-test"
        try:
            r = self.client.get("/dashboard/api/health")
            self.assertEqual(r.status_code, 401)
            r2 = self.client.get(
                "/dashboard/api/health",
                headers={"X-Dashboard-Token": "secret-test"},
            )
            self.assertEqual(r2.status_code, 200)
            r3 = self.client.get(
                "/dashboard/api/health",
                headers={"Authorization": "Bearer secret-test"},
            )
            self.assertEqual(r3.status_code, 200)
            r4 = self.client.get("/dashboard/api/health?token=secret-test")
            self.assertEqual(r4.status_code, 200)
            page = self.client.get("/dashboard?token=secret-test")
            self.assertEqual(page.status_code, 200)
            self.assertIn("bh_dashboard_token", page.cookies)
            r5 = self.client.get(
                "/dashboard/api/health",
                cookies={"bh_dashboard_token": "secret-test"},
            )
            self.assertEqual(r5.status_code, 200)
        finally:
            os.environ["DASHBOARD_TOKEN"] = ""


if __name__ == "__main__":
    unittest.main()
