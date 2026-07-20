"""Merge work logs + shift + templates into final BLok-ready draft."""

from __future__ import annotations

import sqlite3
from datetime import date

from berichtsheft import db, generator
from berichtsheft.ai_gemini import is_enabled as ai_enabled, polish_german
from berichtsheft.blok_hours import stunden_for_blok
from berichtsheft.translate_de import dedupe_lines, translate_note_to_de


def _format_user_logs(logs: list[sqlite3.Row]) -> str:
    if not logs:
        return ""
    bullets = []
    for row in logs:
        content = row["content"].strip()
        if not content or content.lower() in ("cek", "check", "test"):
            continue
        bullets.append(f"• {translate_note_to_de(content)}")
    bullets = dedupe_lines(bullets)
    if not bullets:
        return ""
    return "Eigene Tätigkeiten (Azubi):\n" + "\n".join(bullets)


def finish_day(
    conn: sqlite3.Connection,
    iso_date: str,
    summary: str | None = None,
) -> dict:
    """
    Orchestrate: base generator draft + work logs + optional summary.
    Returns draft dict; sets status pending_review.
    """
    shift = db.get_shift(conn, iso_date)
    if not shift:
        raise ValueError(
            f"Tidak ada shift untuk {iso_date}. Import jadwal EdTime dulu."
        )

    base = generator.generate_for_date(conn, iso_date)
    if not base:
        raise ValueError(f"Tidak bisa generate untuk {iso_date}")

    if base.get("skip_blok"):
        db.save_draft(
            conn,
            iso_date,
            None,
            base["ort"],
            base.get("lernfeld"),
            base["taetigkeiten"],
            status="skipped",
        )
        db.set_approval(conn, iso_date, "skipped", "frei")
        return {**base, "status": "skipped"}

    logs = db.work_logs_for_date(conn, iso_date)
    extra_parts = []
    log_block = _format_user_logs(logs)
    if log_block:
        extra_parts.append(log_block)
    if summary and summary.strip():
        extra_parts.append(f"Zusammenfassung: {translate_note_to_de(summary)}")

    taetigkeiten = base["taetigkeiten"]
    if extra_parts:
        taetigkeiten = taetigkeiten + "\n\n" + "\n\n".join(extra_parts)

    ai_used = False
    if ai_enabled() and not base.get("skip_blok"):
        ctx = f"{iso_date} {base.get('ort')} {base.get('hours') or ''}"
        taetigkeiten, ai_used = polish_german(taetigkeiten, context=ctx)

    blok_hours = stunden_for_blok(conn, iso_date, summary)

    db.save_draft(
        conn,
        iso_date,
        blok_hours or base.get("hours"),
        base["ort"],
        base.get("lernfeld"),
        taetigkeiten,
        status="pending_review",
    )
    db.set_approval(conn, iso_date, "pending", None)

    return {
        **base,
        "taetigkeiten": taetigkeiten,
        "status": "pending_review",
        "log_count": len(logs),
        "ai_polish": ai_used,
    }


def approve_day(conn: sqlite3.Connection, iso_date: str, note: str | None = None) -> dict:
    draft = db.get_draft(conn, iso_date)
    if not draft:
        raise ValueError(f"No draft for {iso_date}")
    db.update_draft_status(conn, iso_date, "approved")
    db.set_approval(conn, iso_date, "approved", note)
    return {
        "date": iso_date,
        "status": "approved",
        "taetigkeiten": draft["taetigkeiten"],
    }


def apply_correction(
    conn: sqlite3.Connection,
    iso_date: str,
    correction: str,
) -> dict:
    draft = db.get_draft(conn, iso_date)
    if not draft:
        raise ValueError(
            f"Tidak ada draft untuk {iso_date}. Jalankan /selesai dulu (hari kerja, bukan libur)."
        )
    if draft["status"] == "skipped":
        raise ValueError(
            f"{iso_date} adalah hari libur di jadwal — tidak ada teks BLok untuk dikoreksi."
        )

    instruction = correction.strip()
    text = draft["taetigkeiten"]
    ai_used = False
    if ai_enabled():
        text, ai_used = polish_german(text, instruction=instruction)
    else:
        text = text + "\n\n(Korrektur): " + translate_note_to_de(instruction)

    db.save_draft(
        conn,
        iso_date,
        draft["hours"],
        draft["ort"],
        draft["lernfeld"],
        text,
        status="pending_review",
    )
    return {
        "date": iso_date,
        "taetigkeiten": text,
        "status": "pending_review",
        "ai_polish": ai_used,
        "weekday": "",
        "ort": draft["ort"],
        "hours": draft["hours"],
    }


def today_iso() -> str:
    return date.today().isoformat()
