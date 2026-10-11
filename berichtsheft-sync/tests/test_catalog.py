"""Tests for katalog kegiatan per Abteilung."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from berichtsheft import catalog, db
from berichtsheft.blok_mapping import load_blok_mapping


class TestCatalog(unittest.TestCase):
    def test_load_and_iter_codes(self) -> None:
        data = catalog.load_katalog()
        codes = catalog.iter_codes(data)
        code_names = {c["code"] for c in codes}
        self.assertIn("BRF", code_names)
        self.assertIn("BAF", code_names)
        self.assertIn("Rezeption", code_names)
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

    def test_rezeption_abteilung(self) -> None:
        rez = next(c for c in catalog.iter_codes() if c["code"] == "Rezeption")
        self.assertEqual(rez["blok_name"], "Rezeption")
        self.assertEqual(rez["department"], "Rezeption")
        self.assertEqual(rez["lernfeld"], "Gästeservice und Kommunikation / Empfang")
        self.assertIn("Rez", rez["aliases"])
        for keyword in (
            "rezeption",
            "empfang",
            "check-in",
            "check-out",
            "reservierung",
            "gäste",
            "telefon",
            "rez",
        ):
            self.assertIn(keyword, rez["keywords"])
        self.assertGreaterEqual(len(rez["default_activities_de"]), 1)
        self.assertGreaterEqual(len(rez["templates_de"]), 5)
        self.assertLessEqual(len(rez["templates_de"]), 8)
        rez_ids = [c["id"] for c in rez["conditions"]]
        self.assertIn("check-in-rush", rez_ids)
        for needed in (
            "check-in-rush",
            "check-out",
            "phone",
            "reservation-change",
            "complaint",
            "night-audit",
            "quiet-shift",
            "group-arrival",
        ):
            self.assertIn(needed, rez_ids)
        rush = next(c for c in rez["conditions"] if c["id"] == "check-in-rush")
        self.assertEqual(rush["when"]["day_type"], "arbeit")
        self.assertEqual(rush["when"]["time_band"], "spaet")
        self.assertIn("check-in", rush["when"]["guest_situation"])
        self.assertGreaterEqual(len(rush["texts_de"]), 2)
        self.assertLessEqual(len(rush["texts_de"]), 4)
        mapping = load_blok_mapping()
        self.assertEqual(mapping["abteilung"]["Rezeption"], "Rezeption")
        self.assertEqual(mapping["abteilung"]["Rez"], "Rezeption")

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

            rez = next(c for c in catalog.iter_codes() if c["code"] == "Rezeption")
            rez_row = conn.execute(
                "SELECT * FROM work_areas WHERE code = ?", ("Rezeption",)
            ).fetchone()
            stored = json.loads(rez_row["conditions_json"])
            self.assertIn("check-in-rush", [c["id"] for c in stored])
            # conditions stay out of the default template pool
            rez_templates = conn.execute(
                "SELECT COUNT(*) AS n FROM activity_templates WHERE code = ?",
                ("Rezeption",),
            ).fetchone()
            self.assertEqual(rez_templates["n"], len(rez["templates_de"]))
            self.assertGreaterEqual(stats["conditions"], 8)
            conn.close()

    def test_format_text_contains_abteilung(self) -> None:
        text = catalog.format_catalog_text()
        self.assertIn("Service", text)
        self.assertIn("Rezeption", text)
        self.assertIn("Housekeeping", text)
        self.assertIn("Tagungen", text)
        self.assertIn("BRF", text)
        self.assertIn("check-in-rush", text)

    def test_every_code_has_editable_conditions(self) -> None:
        codes = catalog.iter_codes()
        self.assertEqual(
            {c["code"] for c in codes},
            {
                "BRF",
                "BAF",
                "Rezeption",
                "Housekeeping",
                "Tagungen",
                "BRE+TG MEP",
                "FS2",
                "Schule",
                "frei",
            },
        )
        catalog.validate_katalog(catalog.load_katalog())
        for item in codes:
            conds = item["conditions"]
            self.assertGreaterEqual(len(conds), 1, item["code"])
            self.assertEqual(len(conds), len({c["id"] for c in conds}))
            for cond in conds:
                self.assertGreaterEqual(len(cond["texts_de"]), 2)
                self.assertLessEqual(len(cond["texts_de"]), 4)
                self.assertIn("day_type", cond["when"])

    def test_markdown_documents_condition_edit_path(self) -> None:
        md = catalog.format_catalog_markdown()
        self.assertIn("data/katalog_abteilung.json", md)
        self.assertIn("check-in-rush", md)
        self.assertIn("day_type=arbeit", md)
        self.assertIn("Conditions bearbeiten", md)
        self.assertIn("templates_de", md)

    def test_save_rejects_bad_condition_and_keeps_templates(self) -> None:
        data = catalog.load_katalog()
        broken = json.loads(json.dumps(data))
        broken["abteilungen"][1]["codes"][0]["conditions"][0]["texts_de"] = ["nur ein Satz"]
        with self.assertRaises(ValueError):
            catalog.validate_katalog(broken)
        # legacy shape without conditions still loads into the DB
        legacy = {
            "abteilungen": [
                {
                    "blok_name": "Service",
                    "codes": [
                        {
                            "code": "BRF",
                            "name_de": "Frühstück",
                            "department": "F&B",
                            "templates_de": ["Satz eins.", "Satz zwei."],
                            "keywords": ["buffet"],
                            "default_activities_de": ["Frühstück"],
                        }
                    ],
                }
            ]
        }
        catalog.validate_katalog(legacy)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.db"
            conn = db.connect(path)
            stats = catalog.sync_to_db(conn, legacy)
            self.assertEqual(stats["templates"], 2)
            self.assertEqual(stats["conditions"], 0)
            conn.close()


if __name__ == "__main__":
    unittest.main()
