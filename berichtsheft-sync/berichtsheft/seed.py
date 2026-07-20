"""Load templates, areas, and shift JSON into SQLite."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from berichtsheft import catalog, db

ROOT = Path(__file__).resolve().parent.parent


def load_templates(conn: sqlite3.Connection, path: Path | None = None) -> int:
    """Load templates from katalog (preferred) or legacy templates JSON."""
    if path is None and catalog.KATALOG_PATH.is_file():
        result = catalog.sync_to_db(conn)
        return result["templates"]

    path = path or ROOT / "data" / "templates_hotelfach.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM activity_templates")
    count = 0
    for item in data["templates"]:
        for text in item["texts"]:
            db.upsert_template(
                conn,
                item["code"],
                item.get("department"),
                item.get("lernfeld"),
                text,
            )
            count += 1
    conn.commit()
    return count


def load_shifts(conn: sqlite3.Connection, path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    count = 0
    for shift in data["shifts"]:
        db.upsert_shift(
            conn,
            {
                "date": shift["date"],
                "day_type": shift["day_type"],
                "start": shift.get("start"),
                "end": shift.get("end"),
                "tags": shift.get("tags", []),
                "segments": shift.get("segments", []),
                "source": data.get("source", "import"),
            },
        )
        count += 1
    conn.commit()
    return count


def bootstrap(conn: sqlite3.Connection) -> None:
    db.init_schema(conn)
    if catalog.KATALOG_PATH.is_file():
        stats = catalog.sync_to_db(conn)
        catalog.export_legacy_files()
        print(f"✓ {stats['templates']} Vorlagen + {stats['areas']} areas dari katalog")
    else:
        templates = load_templates(conn)
        print(f"✓ {templates} Vorlagen geladen")
    shifts_path = ROOT / "data" / "shifts_kw23_24.json"
    shifts = load_shifts(conn, shifts_path)
    print(f"✓ {shifts} Schichten aus {shifts_path.name}")
