"""Tests for Cloud ↔ Mac sync push/pull."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from berichtsheft import catalog, db, sync_bridge
from berichtsheft.api_server import app


class TestSyncBridge(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self.db_path = self.tmp / "sync.db"
        self.katalog_path = self.tmp / "katalog_abteilung.json"
        original = catalog.load_katalog()
        self.katalog_path.write_text(
            json.dumps(original, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.client = TestClient(app)
        os.environ["DASHBOARD_TOKEN"] = "sync-test-token"
        os.environ["SYNC_TOKEN"] = ""

        self.patches = [
            mock.patch.object(db, "DEFAULT_DB", self.db_path),
            mock.patch.object(sync_bridge, "ROOT", self.tmp),
            mock.patch.object(sync_bridge, "SYNC_CONFIG_PATH", self.tmp / "sync_config.json"),
            mock.patch.object(catalog, "KATALOG_PATH", self.katalog_path),
            mock.patch.object(catalog, "AREAS_PATH", self.tmp / "areas_hotel.json"),
            mock.patch.object(catalog, "TEMPLATES_PATH", self.tmp / "templates_hotelfach.json"),
        ]
        for p in self.patches:
            p.start()

        conn = db.connect()
        db.init_schema(conn)
        db.upsert_shift(
            conn,
            {
                "date": "2026-06-04",
                "day_type": "arbeit",
                "start": "08:00",
                "end": "16:00",
                "tags": ["BRF"],
                "segments": [],
                "source": "test",
            },
        )
        conn.commit()
        db.add_work_log(conn, "2026-06-04", "Test log sync", source="test")
        db.save_draft(
            conn,
            "2026-06-04",
            "8",
            "Betrieb",
            None,
            "Buffet vorbereitet.",
            status="draft",
        )
        conn.close()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        os.environ["DASHBOARD_TOKEN"] = ""
        os.environ["SYNC_TOKEN"] = ""
        self._tmpdir.cleanup()

    def _auth(self) -> dict[str, str]:
        return {"Authorization": "Bearer sync-test-token"}

    def test_sync_requires_token(self) -> None:
        os.environ["DASHBOARD_TOKEN"] = ""
        os.environ["SYNC_TOKEN"] = ""
        r = self.client.get("/sync/pull")
        self.assertEqual(r.status_code, 503)

    def test_sync_reject_bad_token(self) -> None:
        r = self.client.get("/sync/pull", headers={"Authorization": "Bearer wrong"})
        self.assertEqual(r.status_code, 401)

    def test_pull_and_push_roundtrip(self) -> None:
        r = self.client.get("/sync/pull", headers=self._auth())
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["schema_version"], 1)
        self.assertGreaterEqual(payload["counts"]["shifts"], 1)
        self.assertGreaterEqual(payload["counts"]["work_logs"], 1)
        self.assertGreaterEqual(payload["counts"]["drafts"], 1)

        # second DB: apply via push
        other = self.tmp / "other.db"
        with mock.patch.object(db, "DEFAULT_DB", other):
            r2 = self.client.post(
                "/sync/push",
                headers=self._auth(),
                json={**payload, "mode": "merge"},
            )
            self.assertEqual(r2.status_code, 200)
            stats = r2.json()["stats"]
            self.assertGreaterEqual(stats["shifts_upserted"], 1)
            self.assertGreaterEqual(stats["work_logs_added"], 1)
            self.assertGreaterEqual(stats["drafts_upserted"], 1)

            conn = db.connect()
            db.init_schema(conn)
            self.assertIsNotNone(db.get_shift(conn, "2026-06-04"))
            self.assertEqual(len(db.work_logs_for_date(conn, "2026-06-04")), 1)
            self.assertIsNotNone(db.get_draft(conn, "2026-06-04"))
            conn.close()

    def test_status_endpoint(self) -> None:
        r = self.client.get("/sync/status", headers=self._auth())
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["token_configured"])
        self.assertIn("local_counts", data)

    def test_dashboard_sync_config(self) -> None:
        r = self.client.put(
            "/dashboard/api/sync/config",
            headers=self._auth(),
            json={"remote_api_url": "https://example.trycloudflare.com"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["remote_api_url"], "https://example.trycloudflare.com")
        cfg = sync_bridge.load_sync_config()
        self.assertEqual(cfg["remote_api_url"], "https://example.trycloudflare.com")

        r2 = self.client.get("/dashboard/api/sync", headers=self._auth())
        self.assertEqual(r2.status_code, 200)
        self.assertIn("example.trycloudflare.com", r2.json()["remote_api_url"])


if __name__ == "__main__":
    unittest.main()
