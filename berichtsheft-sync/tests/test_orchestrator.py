import sqlite3
import tempfile
import unittest
from pathlib import Path

from berichtsheft import db, orchestrator
from berichtsheft.blok_worker import dry_run_fill
from berichtsheft.seed import bootstrap, load_shifts

ROOT = Path(__file__).resolve().parent.parent


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.conn = sqlite3.connect(self.tmp.name)
        self.conn.row_factory = sqlite3.Row
        db.init_schema(self.conn)
        bootstrap(self.conn)
        load_shifts(self.conn, ROOT / "data" / "shifts_kw23_24.json")

    def tearDown(self):
        self.conn.close()
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_finish_with_logs(self):
        db.add_work_log(self.conn, "2026-06-04", "Tagung coffee", source="test")
        draft = orchestrator.finish_day(self.conn, "2026-06-04", "Selesai")
        self.assertIn("Tagung", draft["taetigkeiten"])
        self.assertNotIn("ruang", draft["taetigkeiten"].lower())
        self.assertEqual(draft["status"], "pending_review")

    def test_finish_frei_skipped(self):
        draft = orchestrator.finish_day(self.conn, "2026-06-02")
        self.assertTrue(draft.get("skip_blok"))

    def test_dry_run_worker(self):
        orchestrator.finish_day(self.conn, "2026-06-05", "BRF+HK")
        path = dry_run_fill(self.conn, "2026-06-05")
        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
