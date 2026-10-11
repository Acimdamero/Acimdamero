"""Date validation and dashboard day-fill (sqlite temp, no live BLok)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from berichtsheft import blok_worker, db, day_fill
from berichtsheft.api_server import app

PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
NO_CREDS = {"credential_resolvable": False, "source": "none"}


class TestDayValidation(unittest.TestCase):
    def test_parse_iso_date(self) -> None:
        self.assertEqual(day_fill.parse_iso_date("2026-06-02"), "2026-06-02")
        for bad in ("", "2026-6-2", "11-10-2026", "2026-13-01", "2026-02-31", "hari"):
            with self.assertRaises(day_fill.DayValidationError):
                day_fill.parse_iso_date(bad)

    def test_parse_hours_and_mode(self) -> None:
        self.assertEqual(day_fill.parse_hhmm("8:05", "start_time"), "08:05")
        self.assertEqual(day_fill.parse_hhmm("22:00:00", "end_time"), "22:00")
        with self.assertRaises(day_fill.DayValidationError):
            day_fill.parse_hhmm("25:00", "start_time")
        self.assertEqual(day_fill.parse_fill_mode("dry-run"), "dry_run")
        with self.assertRaises(day_fill.DayValidationError):
            day_fill.parse_fill_mode("push")
        overnight = day_fill.clock_duration("22:00", "06:00")
        self.assertEqual(overnight["minutes"], 8 * 60)
        self.assertEqual(overnight["label"], "8h:00min")


class TestDashboardDayApi(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        os.environ["DASHBOARD_TOKEN"] = ""

    def tearDown(self) -> None:
        os.environ["DASHBOARD_TOKEN"] = ""

    def test_page_has_hari_tab(self) -> None:
        page = self.client.get("/dashboard")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Hari &amp; BLok", page.text)
        self.assertIn("Isi BLok (dry-run)", page.text)
        self.assertIn("Isi BLok live", page.text)
        self.assertIn('data-panel="hari"', page.text)

    def test_invalid_date_payload(self) -> None:
        missing = self.client.get("/dashboard/api/day")
        self.assertEqual(missing.status_code, 400)
        bad = self.client.get("/dashboard/api/day?date=2026-02-31")
        self.assertEqual(bad.status_code, 400)
        self.assertIn("date", bad.json()["detail"])
        logged = self.client.post(
            "/dashboard/api/day/log",
            json={"date": "2026/06/02", "text": "halo"},
        )
        self.assertEqual(logged.status_code, 400)
        empty = self.client.post(
            "/dashboard/api/day/log",
            json={"date": "2026-06-02", "text": "   "},
        )
        self.assertEqual(empty.status_code, 400)
        hours = self.client.put(
            "/dashboard/api/day/hours",
            json={"date": "2026-06-02", "start_time": "25:00", "end_time": "16:00"},
        )
        self.assertEqual(hours.status_code, 400)

    def test_token_required(self) -> None:
        os.environ["DASHBOARD_TOKEN"] = "secret-day"
        try:
            denied = self.client.get("/dashboard/api/day?date=2026-06-02")
            self.assertEqual(denied.status_code, 401)
            allowed = self.client.get(
                "/dashboard/api/day?date=2026-06-02",
                headers={"X-Dashboard-Token": "secret-day"},
            )
            self.assertEqual(allowed.status_code, 200, allowed.text)
        finally:
            os.environ["DASHBOARD_TOKEN"] = ""

    def test_save_log_hours_dry_run_and_photo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "hari.db"
            out = root / "dry"
            photos = root / "attachments"
            out.mkdir()
            with mock.patch.object(db, "DEFAULT_DB", db_path), mock.patch.object(
                blok_worker, "OUTPUT_DIR", out
            ), mock.patch(
                "berichtsheft.dashboard.ATTACHMENTS_DIR", photos
            ), mock.patch(
                "berichtsheft.orchestrator.ai_enabled", return_value=False
            ), mock.patch(
                "berichtsheft.dashboard._blok_credential_status", return_value=NO_CREDS
            ), mock.patch(
                "berichtsheft.blok_worker.live_fill",
                side_effect=AssertionError("live fill must not run"),
            ), mock.patch(
                "berichtsheft.day_fill.upload_attachments_for_date",
                side_effect=AssertionError("live upload must not run"),
            ):
                hours = self.client.put(
                    "/dashboard/api/day/hours",
                    json={
                        "date": "2026-06-02",
                        "start_time": "08:00",
                        "end_time": "16:00",
                        "day_type": "arbeit",
                    },
                )
                self.assertEqual(hours.status_code, 200, hours.text)
                self.assertEqual(hours.json()["shift"]["duration_label"], "8h:00min")

                saved = self.client.post(
                    "/dashboard/api/day/log",
                    json={"date": "2026-06-02", "text": "Gäste am Empfang begrüßt."},
                )
                self.assertEqual(saved.status_code, 200, saved.text)
                self.assertEqual(saved.json()["source"], "dashboard")

                conn = db.connect(db_path)
                db.init_schema(conn)
                rows = db.work_logs_for_date(conn, "2026-06-02")
                conn.close()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["content"], "Gäste am Empfang begrüßt.")
                self.assertEqual(rows[0]["source"], "dashboard")

                view = self.client.get("/dashboard/api/day?date=2026-06-02")
                self.assertEqual(view.status_code, 200, view.text)
                body = view.json()
                self.assertEqual(body["weekday_de"], "Dienstag")
                self.assertEqual(body["hours"]["blok_label"], "8h:00min")
                self.assertEqual(len(body["work_logs"]), 1)
                phrase_codes = [group["code"] for group in body["phrases"]]
                for code in ("Rezeption", "BRF", "Housekeeping", "Tagungen", "Schule"):
                    self.assertIn(code, phrase_codes)
                brf = next(group for group in body["phrases"] if group["code"] == "BRF")
                self.assertTrue(brf["for_day"])
                self.assertTrue(brf["symbol"])
                self.assertTrue(brf["buttons"][0]["text"])
                self.assertFalse(body["blok"]["live_available"])

                filled = self.client.post(
                    "/dashboard/api/day/fill",
                    json={"date": "2026-06-02", "mode": "dry_run"},
                )
                self.assertEqual(filled.status_code, 200, filled.text)
                fill_body = filled.json()
                self.assertEqual(fill_body["status_label"], "tersimpan + dry-run")
                self.assertFalse(fill_body["live_sent"])
                html_path = out / "2026-06-02.html"
                self.assertTrue(html_path.is_file())
                html = html_path.read_text(encoding="utf-8")
                self.assertIn("Gäste am Empfang begrüßt.", html)
                self.assertEqual(
                    fill_body["day"]["preview"]["html_url"],
                    "/dashboard/blok-preview/2026-06-02.html",
                )

                live = self.client.post(
                    "/dashboard/api/day/fill",
                    json={
                        "date": "2026-06-03",
                        "mode": "live",
                        "start_time": "09:00",
                        "end_time": "17:00",
                        "day_type": "arbeit",
                    },
                )
                self.assertEqual(live.status_code, 200, live.text)
                live_body = live.json()
                self.assertEqual(live_body["status_label"], "tersimpan + dry-run")
                self.assertTrue(live_body["fallback_dry_run"])
                self.assertFalse(live_body["live_sent"])
                self.assertTrue((out / "2026-06-03.html").is_file())

                photo = self.client.post(
                    "/dashboard/api/day/photo",
                    json={
                        "date": "2026-06-02",
                        "filename": "meja.png",
                        "mime_type": "image/png",
                        "image_base64": PNG_1X1,
                    },
                )
                self.assertEqual(photo.status_code, 200, photo.text)
                self.assertEqual(photo.json()["status_label"], "upload pending")
                self.assertTrue((photos / "2026-06-02" / "meja.png").is_file())

                queued = self.client.post(
                    "/dashboard/api/day/photo/upload-blok",
                    json={"date": "2026-06-02"},
                )
                self.assertEqual(queued.status_code, 200, queued.text)
                self.assertEqual(queued.json()["status_label"], "upload pending")
                self.assertFalse(queued.json()["live"])
                self.assertEqual(queued.json()["results"][0]["blok_status"], "pending")

                conn = db.connect(db_path)
                atts = db.attachments_for_date(conn, "2026-06-02")
                conn.close()
                self.assertEqual(len(atts), 1)
                self.assertEqual(atts[0]["blok_status"], "pending")


if __name__ == "__main__":
    unittest.main()
