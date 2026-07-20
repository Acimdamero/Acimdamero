"""Generate German Berichtsheft draft text from shifts + activity templates."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date

from berichtsheft import db

WEEKDAY_DE = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag",
}


def _pick_text(texts: list[str], seed: str) -> str:
    if not texts:
        return ""
    idx = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(texts)
    return texts[idx]


def _hours_label(start: str | None, end: str | None) -> str | None:
    if start and end:
        return f"{start}–{end} Uhr"
    return None


def _codes_from_shift(shift: sqlite3.Row) -> list[str]:
    if shift["day_type"] == "frei":
        return ["frei"]
    if shift["day_type"] == "schule":
        return ["Schule"]
    tags = json.loads(shift["tags_json"] or "[]")
    segments = json.loads(shift["segments_json"] or "[]")
    codes: list[str] = []
    for seg in segments:
        code = seg.get("code")
        if code and code not in codes:
            codes.append(code)
    for tag in tags:
        if tag not in ("Ausgang",) and tag not in codes:
            codes.append(tag)
    return codes or ["BRF"]


def generate_for_date(conn: sqlite3.Connection, iso_date: str) -> dict | None:
    shift = db.get_shift(conn, iso_date)
    if not shift:
        return None

    d = date.fromisoformat(iso_date)
    weekday = WEEKDAY_DE[d.weekday()]
    codes = _codes_from_shift(shift)

    if shift["day_type"] == "frei":
        return {
            "date": iso_date,
            "weekday": weekday,
            "ort": "Frei",
            "hours": None,
            "lernfeld": None,
            "taetigkeiten": "Frei (Ausgang) laut Dienstplan — kein betrieblicher Nachweis.",
            "codes": codes,
            "skip_blok": True,
        }

    paragraphs: list[str] = []
    lernfelder: set[str] = set()

    for code in codes:
        rows = conn.execute(
            "SELECT * FROM activity_templates WHERE code = ?",
            (code,),
        ).fetchall()
        if not rows:
            paragraphs.append(f"Einsatz im Bereich {code} gemäß Dienstplan.")
            continue
        texts = [r["text_de"] for r in rows]
        lernfeld = rows[0]["lernfeld"]
        if lernfeld:
            lernfelder.add(lernfeld)
        paragraphs.append(_pick_text(texts, f"{iso_date}:{code}"))

    segments = json.loads(shift["segments_json"] or "[]")
    if segments:
        plan_lines = []
        for seg in segments:
            if seg.get("parallel"):
                plan_lines.append(f"• Zusätzlich: {seg.get('label', seg.get('code'))}")
            elif seg.get("start") and seg.get("end"):
                plan_lines.append(
                    f"• {seg['start']}–{seg['end']}: {seg.get('label', seg.get('code'))}"
                )
        if plan_lines:
            paragraphs.insert(0, "Dienstplan:\n" + "\n".join(plan_lines))

    if shift["day_type"] == "schule":
        ort = "Berufsschule"
    else:
        ort = "Betrieb"

    hours = _hours_label(shift["start_time"], shift["end_time"])
    lernfeld = "; ".join(sorted(lernfelder)) if lernfelder else None

    return {
        "date": iso_date,
        "weekday": weekday,
        "ort": ort,
        "hours": hours,
        "lernfeld": lernfeld,
        "taetigkeiten": "\n\n".join(paragraphs),
        "codes": codes,
        "skip_blok": shift["day_type"] == "frei",
    }


def generate_range(conn: sqlite3.Connection, start: str, end: str) -> list[dict]:
    results = []
    for row in db.shifts_in_range(conn, start, end):
        draft = generate_for_date(conn, row["date"])
        if draft:
            db.save_draft(
                conn,
                draft["date"],
                draft.get("hours"),
                draft["ort"],
                draft.get("lernfeld"),
                draft["taetigkeiten"],
            )
            results.append(draft)
    return results


def parse_week(iso_week: str) -> tuple[str, str]:
    """ISO week like 2026-W23 -> Monday..Sunday dates."""
    normalized = iso_week.upper().strip()
    if "-W" not in normalized:
        raise ValueError(f"Ungültige KW: {iso_week} (erwartet z.B. 2026-W23)")
    year_s, week_s = normalized.split("-W", 1)
    year, week = int(year_s), int(week_s)
    start = date.fromisocalendar(year, week, 1)
    end = date.fromisocalendar(year, week, 7)
    return start.isoformat(), end.isoformat()


def format_preview(draft: dict) -> str:
    lines = [
        f"{'═' * 60}",
        f"  {draft['date']} ({draft['weekday']})",
        f"  Ort: {draft['ort']}",
    ]
    if draft.get("hours"):
        lines.append(f"  Arbeitszeit: {draft['hours']}")
    if draft.get("lernfeld"):
        lines.append(f"  Lernfeld: {draft['lernfeld']}")
    if draft.get("codes"):
        lines.append(f"  Codes: {', '.join(draft['codes'])}")
    if draft.get("skip_blok"):
        lines.append("  ⚠ Nicht in BLok eintragen (Frei)")
    lines.append("─" * 60)
    lines.append(draft["taetigkeiten"])
    return "\n".join(lines)
