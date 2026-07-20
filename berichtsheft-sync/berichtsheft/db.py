"""SQLite persistence for shifts, templates, and generated drafts."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(__file__).resolve().parent.parent / "berichtsheft.db"


def connect(db_path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS activity_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            department TEXT,
            lernfeld TEXT,
            text_de TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            day_type TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            tags_json TEXT,
            segments_json TEXT,
            source TEXT DEFAULT 'import'
        );

        CREATE TABLE IF NOT EXISTS draft_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            hours TEXT,
            ort TEXT NOT NULL,
            lernfeld TEXT,
            taetigkeiten TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            generated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS work_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT DEFAULT 'cli',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS approvals (
            date TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'pending',
            note TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS work_areas (
            code TEXT PRIMARY KEY,
            name_de TEXT,
            keywords_json TEXT,
            default_activities_json TEXT
        );

        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            path TEXT NOT NULL,
            caption TEXT,
            kind TEXT DEFAULT 'photo',
            vision_mode TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_shifts_date ON shifts(date);
        CREATE INDEX IF NOT EXISTS idx_drafts_date ON draft_entries(date);
        CREATE INDEX IF NOT EXISTS idx_work_logs_date ON work_logs(date);
        """
    )
    _migrate_schema(conn)
    conn.commit()


def _migrate_schema(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(attachments)")}
    for col, typ in (
        ("blok_filename", "TEXT"),
        ("blok_status", "TEXT"),
        ("blok_uploaded_at", "TEXT"),
        ("blok_bound_at", "TEXT"),
    ):
        if col not in cols:
            conn.execute(f"ALTER TABLE attachments ADD COLUMN {col} {typ}")


def upsert_template(
    conn: sqlite3.Connection,
    code: str,
    department: str | None,
    lernfeld: str | None,
    text_de: str,
) -> None:
    conn.execute(
        """
        INSERT INTO activity_templates (code, department, lernfeld, text_de)
        VALUES (?, ?, ?, ?)
        """,
        (code, department, lernfeld, text_de),
    )


def upsert_shift(conn: sqlite3.Connection, row: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO shifts (date, day_type, start_time, end_time, tags_json, segments_json, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            day_type=excluded.day_type,
            start_time=excluded.start_time,
            end_time=excluded.end_time,
            tags_json=excluded.tags_json,
            segments_json=excluded.segments_json,
            source=excluded.source
        """,
        (
            row["date"],
            row["day_type"],
            row.get("start"),
            row.get("end"),
            json.dumps(row.get("tags") or [], ensure_ascii=False),
            json.dumps(row.get("segments") or [], ensure_ascii=False),
            row.get("source", "import"),
        ),
    )


def get_shift(conn: sqlite3.Connection, date: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM shifts WHERE date = ?", (date,)).fetchone()


def shifts_in_range(conn: sqlite3.Connection, start: str, end: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM shifts WHERE date >= ? AND date <= ? ORDER BY date",
            (start, end),
        )
    )


def templates_for_codes(conn: sqlite3.Connection, codes: list[str]) -> list[sqlite3.Row]:
    if not codes:
        return []
    placeholders = ",".join("?" * len(codes))
    return list(
        conn.execute(
            f"SELECT * FROM activity_templates WHERE code IN ({placeholders})",
            codes,
        )
    )


def save_draft(
    conn: sqlite3.Connection,
    date: str,
    hours: str | None,
    ort: str,
    lernfeld: str | None,
    taetigkeiten: str,
    status: str = "draft",
) -> None:
    conn.execute(
        """
        INSERT INTO draft_entries (date, hours, ort, lernfeld, taetigkeiten, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            hours=excluded.hours,
            ort=excluded.ort,
            lernfeld=excluded.lernfeld,
            taetigkeiten=excluded.taetigkeiten,
            status=excluded.status,
            generated_at=datetime('now')
        """,
        (date, hours, ort, lernfeld, taetigkeiten, status),
    )
    conn.commit()


def add_work_log(
    conn: sqlite3.Connection,
    date: str,
    content: str,
    source: str = "cli",
) -> int:
    cur = conn.execute(
        "INSERT INTO work_logs (date, content, source) VALUES (?, ?, ?)",
        (date, content, source),
    )
    conn.commit()
    return int(cur.lastrowid)


def work_logs_for_date(conn: sqlite3.Connection, date: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM work_logs WHERE date = ? ORDER BY created_at",
            (date,),
        )
    )


def set_approval(
    conn: sqlite3.Connection,
    date: str,
    status: str,
    note: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO approvals (date, status, note)
        VALUES (?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            status=excluded.status,
            note=excluded.note,
            updated_at=datetime('now')
        """,
        (date, status, note),
    )
    conn.commit()


def get_approval(conn: sqlite3.Connection, date: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM approvals WHERE date = ?", (date,)).fetchone()


def upsert_area(
    conn: sqlite3.Connection,
    code: str,
    name_de: str,
    keywords: list[str],
    default_activities: list[str],
) -> None:
    conn.execute(
        """
        INSERT INTO work_areas (code, name_de, keywords_json, default_activities_json)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(code) DO UPDATE SET
            name_de=excluded.name_de,
            keywords_json=excluded.keywords_json,
            default_activities_json=excluded.default_activities_json
        """,
        (
            code,
            name_de,
            json.dumps(keywords, ensure_ascii=False),
            json.dumps(default_activities, ensure_ascii=False),
        ),
    )
    conn.commit()


def update_draft_status(conn: sqlite3.Connection, date: str, status: str) -> None:
    conn.execute(
        "UPDATE draft_entries SET status = ? WHERE date = ?",
        (status, date),
    )
    conn.commit()


def get_draft(conn: sqlite3.Connection, date: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM draft_entries WHERE date = ?", (date,)).fetchone()


def drafts_in_range(conn: sqlite3.Connection, start: str, end: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM draft_entries WHERE date >= ? AND date <= ? ORDER BY date",
            (start, end),
        )
    )


def add_attachment(
    conn: sqlite3.Connection,
    date: str,
    path: str,
    caption: str | None = None,
    kind: str = "photo",
    vision_mode: str | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO attachments (date, path, caption, kind, vision_mode)
        VALUES (?, ?, ?, ?, ?)
        """,
        (date, path, caption, kind, vision_mode),
    )
    conn.commit()
    return int(cur.lastrowid)


def attachments_for_date(conn: sqlite3.Connection, date: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM attachments WHERE date = ? ORDER BY created_at",
            (date,),
        )
    )


def get_attachment(conn: sqlite3.Connection, attachment_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM attachments WHERE id = ?", (attachment_id,)
    ).fetchone()


def update_attachment_blok(
    conn: sqlite3.Connection,
    attachment_id: int,
    status: str,
    *,
    blok_filename: str | None = None,
    uploaded_at: str | None = None,
    bound_at: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE attachments SET
            blok_status = ?,
            blok_filename = COALESCE(?, blok_filename),
            blok_uploaded_at = COALESCE(?, blok_uploaded_at),
            blok_bound_at = COALESCE(?, blok_bound_at)
        WHERE id = ?
        """,
        (status, blok_filename, uploaded_at, bound_at, attachment_id),
    )
    conn.commit()
