"""Tests for katalog kegiatan per Abteilung."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from berichtsheft import catalog, db


class TestCatalog(unittest.TestCase):
    def test_load_and_iter_codes(self) -> None:
        data = catalog.load_katalog()
        codes = catalog.iter_codes(data)
        code_names = {c["code"] for c in codes}
        self.assertIn("BRF", code_names)
        self.assertIn("BAF", code_names)
        self.assertIn("Housekeeping", code_names)
        self.assertIn("Tagungen", code_names)
        self.assertIn("BRE+TG MEP", code_names)
        self.assertIn("FS2", code_names)
        self.assertIn("Schule", code_names)
        self.assertIn("frei", code_names)

    def test_brf_is_service(self) -> None:
        brf = next(c for c in catalog.iter_codes() if c["code"] == "BRF")
        self.assertEqual(brf["blok_name"], "Service")
        self.assertGreaterEqual(len(brf["templates_de"]), 3)

    def test_sync_to_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.db"
            conn = db.connect(path)
            stats = catalog.sync_to_db(conn)
            self.assertGreater(stats["templates"], 10)
            self.assertGreaterEqual(stats["areas"], 8)

            rows = conn.execute(
                "SELECT COUNT(*) AS n FROM activity_templates WHERE code = ?",
                ("BRF",),
            ).fetchone()
            self.assertGreaterEqual(rows["n"], 3)

            hk = conn.execute(
                "SELECT * FROM work_areas WHERE code = ?", ("HK",)
            ).fetchone()
            self.assertIsNotNone(hk)
            keywords = json.loads(hk["keywords_json"])
            self.assertIn("housekeeping", keywords)
            conn.close()

    def test_format_text_contains_abteilung(self) -> None:
        text = catalog.format_catalog_text()
        self.assertIn("Service", text)
        self.assertIn("Housekeeping", text)
        self.assertIn("Tagungen", text)
        self.assertIn("BRF", text)


if __name__ == "__main__":
    unittest.main()
