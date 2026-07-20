"""Load work area map from katalog (preferred) or legacy JSON."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from berichtsheft import catalog, db

ROOT = Path(__file__).resolve().parent.parent


def load_areas_file(conn: sqlite3.Connection, path: Path | None = None) -> int:
    if path is None and catalog.KATALOG_PATH.is_file():
        return catalog.sync_to_db(conn)["areas"]

    path = path or ROOT / "data" / "areas_hotel.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    count = 0
    for area in data.get("areas", []):
        db.upsert_area(
            conn,
            area["code"],
            area.get("name_de", area["code"]),
            area.get("keywords", []),
            area.get("default_activities_de", []),
        )
        count += 1
    return count
