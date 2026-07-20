"""Jam kerja untuk field BLok — default 8 jam, kecuali lembur."""

from __future__ import annotations

import re
import sqlite3

from berichtsheft import db

DEFAULT_STUNDEN = "8h:00min"
LEMBUR_KEYWORDS = ("lembur", "überstunden", "uberstunden", "overtime", "mehr gearbeitet")


def _minutes_from_shift(shift: sqlite3.Row) -> int | None:
    start, end = shift["start_time"], shift["end_time"]
    if not start or not end:
        return None
    m = re.match(r"(\d{1,2}):(\d{2})", start)
    n = re.match(r"(\d{1,2}):(\d{2})", end)
    if not m or not n:
        return None
    s = int(m.group(1)) * 60 + int(m.group(2))
    e = int(n.group(1)) * 60 + int(n.group(2))
    if e < s:
        e += 24 * 60
    return e - s


def _format_blok_minutes(minutes: int) -> str:
    return f"{minutes // 60}h:{minutes % 60:02d}min"


def _has_lembur_hint(logs: list[sqlite3.Row], summary: str | None) -> bool:
    blob = " ".join(row["content"] for row in logs)
    if summary:
        blob += " " + summary
    low = blob.lower()
    return any(k in low for k in LEMBUR_KEYWORDS)


def stunden_for_blok(
    conn: sqlite3.Connection,
    iso_date: str,
    summary: str | None = None,
) -> str | None:
    """
    Aturan hotel/Azubi:
    - Hari aktif (arbeit / schule) dengan jadwal → 8h:00min di BLok
    - Kecuali lembur disebutkan di log/summary → jam aktual dari EdTime
    """
    shift = db.get_shift(conn, iso_date)
    if not shift:
        return None
    if shift["day_type"] == "frei":
        return None

    logs = db.work_logs_for_date(conn, iso_date)
    if _has_lembur_hint(logs, summary):
        mins = _minutes_from_shift(shift)
        if mins and mins > 8 * 60:
            return _format_blok_minutes(mins)
        if mins:
            return _format_blok_minutes(mins)

    return DEFAULT_STUNDEN
