"""Day view for the dashboard: logs, hours, phrase chips, photos, BLok fill."""

from __future__ import annotations

import base64
import json
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from berichtsheft import blok_worker, catalog, db, generator, orchestrator
from berichtsheft.blok_hours import (
    _format_blok_minutes,
    _minutes_from_shift,
    stunden_for_blok,
)
from berichtsheft.blok_upload import upload_attachments_for_date

WEEKDAY_DE = (
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
)
WEEKDAY_ID = ("Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu")

# Always offered so the composer can pull Berichtsheft sentences even before a shift exists.
CORE_CODES = ("Rezeption", "BRF", "Housekeeping", "Tagungen", "Schule")

CODE_SYMBOLS = {
    "Rezeption": "🛎️",
    "BRF": "🍳",
    "BAF": "🍽️",
    "Housekeeping": "🛏️",
    "Tagungen": "📋",
    "BRE+TG MEP": "🥂",
    "FS2": "☕",
    "Schule": "🎓",
}

DAY_TYPES = ("arbeit", "schule", "frei")
MAX_PHOTO_BYTES = 15 * 1024 * 1024
MIME_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HHMM = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")

STATUS_SAVED_DRY_RUN = "tersimpan + dry-run"
STATUS_LIVE_SENT = "live terkirim"
STATUS_UPLOAD_PENDING = "upload pending"
STATUS_SAVED = "tersimpan"
STATUS_SKIPPED = "tersimpan (libur, tidak diisi BLok)"


class DayValidationError(ValueError):
    """Invalid date, hours, or day payload from the dashboard."""


def parse_iso_date(value: str | None) -> str:
    raw = (value or "").strip()
    if not _ISO_DATE.match(raw):
        raise DayValidationError("date harus YYYY-MM-DD")
    try:
        date.fromisoformat(raw)
    except ValueError as e:
        raise DayValidationError("date tidak valid") from e
    return raw


def parse_hhmm(value: str | None, field: str) -> str:
    raw = (value or "").strip()
    match = _HHMM.match(raw)
    if not match:
        raise DayValidationError(f"{field} harus HH:MM")
    hour, minute = int(match.group(1)), int(match.group(2))
    second = int(match.group(3) or 0)
    if hour > 23 or minute > 59 or second > 59:
        raise DayValidationError(f"{field} tidak valid")
    return f"{hour:02d}:{minute:02d}"


def parse_day_type(value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    day_type = str(value).strip().lower()
    if day_type not in DAY_TYPES:
        raise DayValidationError("day_type harus arbeit, schule, atau frei")
    return day_type


def parse_fill_mode(value: str | None) -> str:
    mode = (value or "").strip().lower().replace("-", "_")
    if mode in ("dry_run", "dryrun"):
        return "dry_run"
    if mode == "live":
        return "live"
    raise DayValidationError("mode harus dry_run atau live")


def clock_duration(start: str | None, end: str | None) -> dict[str, Any]:
    minutes = _minutes_from_shift({"start_time": start, "end_time": end})
    if minutes is None:
        return {"minutes": None, "label": None}
    return {"minutes": minutes, "label": _format_blok_minutes(minutes)}


def _json_list(raw: str | None) -> list[Any]:
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _row(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def media_url_for(rel: str | None) -> str | None:
    if not rel:
        return None
    prefix = "data/attachments/"
    if rel.startswith(prefix):
        return "/dashboard/media/" + rel[len(prefix) :]
    return f"/dashboard/media/{rel}"


def _file_exists(repo_root: Path, rel: str | None) -> bool:
    if not rel:
        return False
    path = Path(rel)
    if not path.is_absolute():
        path = (repo_root / rel).resolve()
    else:
        path = path.resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        return path.is_file()
    return path.is_file()


def phrase_groups(katalog: dict[str, Any] | None, day_codes: list[str]) -> list[dict[str, Any]]:
    """Symbol buttons: day's Abteilung codes first, then the core katalog set."""
    by_code = {item["code"]: item for item in catalog.iter_codes(katalog)}
    ordered: list[tuple[str, bool]] = []
    seen: set[str] = set()
    for code in day_codes:
        if code == "frei" or code in seen or code not in by_code:
            continue
        ordered.append((code, True))
        seen.add(code)
    for code in CORE_CODES:
        if code in seen or code not in by_code:
            continue
        ordered.append((code, False))
        seen.add(code)

    groups: list[dict[str, Any]] = []
    for code, for_day in ordered:
        item = by_code[code]
        buttons: list[dict[str, str]] = []
        for cond in item.get("conditions") or []:
            texts = [str(text).strip() for text in (cond.get("texts_de") or []) if str(text).strip()]
            if not texts:
                continue
            buttons.append(
                {
                    "id": str(cond.get("id") or ""),
                    "kind": "condition",
                    "label": str(cond.get("label_de") or cond.get("id") or "Kondisi"),
                    "text": " ".join(texts),
                }
            )
        for index, text in enumerate(item.get("templates_de") or []):
            sentence = str(text).strip()
            if not sentence:
                continue
            buttons.append(
                {
                    "id": f"template-{index}",
                    "kind": "template",
                    "label": f"Vorlage {index + 1}",
                    "text": sentence,
                }
            )
        if not buttons:
            continue
        groups.append(
            {
                "code": code,
                "symbol": CODE_SYMBOLS.get(code, "✦"),
                "name_de": item.get("name_de") or code,
                "blok_name": item.get("blok_name") or "",
                "for_day": for_day,
                "buttons": buttons,
            }
        )
    return groups


def _shift_public(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    duration = clock_duration(row["start_time"], row["end_time"])
    return {
        "date": row["date"],
        "day_type": row["day_type"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "tags": _json_list(row["tags_json"]),
        "segments": _json_list(row["segments_json"]),
        "source": row["source"],
        "duration_minutes": duration["minutes"],
        "duration_label": duration["label"],
    }


def _preview(iso: str, draft: sqlite3.Row | None) -> dict[str, Any]:
    html_path = blok_worker.OUTPUT_DIR / f"{iso}.html"
    shot_path = blok_worker.OUTPUT_DIR / f"{iso}_live.png"
    draft_text = draft["taetigkeiten"] if draft else None
    return {
        "draft_text": draft_text,
        "draft_status": draft["status"] if draft else None,
        "ort": draft["ort"] if draft else None,
        "hours": draft["hours"] if draft else None,
        "lernfeld": draft["lernfeld"] if draft else None,
        "html_url": f"/dashboard/blok-preview/{iso}.html" if html_path.is_file() else None,
        "screenshot_url": (
            f"/dashboard/blok-preview/{iso}_live.png" if shot_path.is_file() else None
        ),
    }


def build_day_view(
    conn: sqlite3.Connection,
    iso: str,
    *,
    repo_root: Path,
    credentials_present: bool,
) -> dict[str, Any]:
    parsed = date.fromisoformat(iso)
    shift_row = db.get_shift(conn, iso)
    shift = _shift_public(shift_row)
    day_codes = generator._codes_from_shift(shift_row) if shift_row else []
    logs = [_row(row) for row in db.work_logs_for_date(conn, iso)]
    draft = db.get_draft(conn, iso)
    attachments = []
    for row in db.attachments_for_date(conn, iso):
        item = _row(row)
        rel = item.get("path") or ""
        item["file_exists"] = _file_exists(repo_root, rel)
        item["media_url"] = media_url_for(rel) if item["file_exists"] else None
        attachments.append(item)

    duration = clock_duration(
        shift["start_time"] if shift else None,
        shift["end_time"] if shift else None,
    )
    blok_label = stunden_for_blok(conn, iso)
    return {
        "ok": True,
        "date": iso,
        "weekday_de": WEEKDAY_DE[parsed.weekday()],
        "weekday_id": WEEKDAY_ID[parsed.weekday()],
        "shift": shift,
        "day_codes": [code for code in day_codes if code != "frei"],
        "hours": {
            "start_time": shift["start_time"] if shift else None,
            "end_time": shift["end_time"] if shift else None,
            "day_type": shift["day_type"] if shift else None,
            "duration_minutes": duration["minutes"],
            "duration_label": duration["label"],
            "blok_label": blok_label,
        },
        "work_logs": logs,
        "draft": _row(draft) if draft else None,
        "attachments": attachments,
        "phrases": phrase_groups(catalog.load_katalog(), day_codes),
        "preview": _preview(iso, draft),
        "blok": {
            "credentials_present": credentials_present,
            "live_available": credentials_present,
            "upload_endpoint": "/attachments/upload-blok",
        },
    }


def save_log(conn: sqlite3.Connection, iso: str, text: str) -> int:
    content = (text or "").strip()
    if not content:
        raise DayValidationError("text kosong")
    return db.add_work_log(conn, iso, content, source="dashboard")


def save_hours(
    conn: sqlite3.Connection,
    iso: str,
    start_time: str,
    end_time: str,
    day_type: str | None = None,
) -> dict[str, Any]:
    start = parse_hhmm(start_time, "start_time")
    end = parse_hhmm(end_time, "end_time")
    chosen = parse_day_type(day_type)
    existing = db.get_shift(conn, iso)
    if existing:
        tags = _json_list(existing["tags_json"])
        segments = _json_list(existing["segments_json"])
        source = existing["source"] or "dashboard"
        resolved_type = chosen or existing["day_type"]
    else:
        tags = []
        segments = []
        source = "dashboard"
        resolved_type = chosen or "arbeit"
    db.upsert_shift(
        conn,
        {
            "date": iso,
            "day_type": resolved_type,
            "start": start,
            "end": end,
            "tags": tags,
            "segments": segments,
            "source": source,
        },
    )
    conn.commit()
    return _shift_public(db.get_shift(conn, iso)) or {}


def apply_optional_hours(
    conn: sqlite3.Connection,
    iso: str,
    start_time: str | None,
    end_time: str | None,
    day_type: str | None,
) -> None:
    if not any((start_time, end_time, day_type)):
        return
    existing = db.get_shift(conn, iso)
    start = start_time or (existing["start_time"] if existing else None)
    end = end_time or (existing["end_time"] if existing else None)
    if not start or not end:
        raise DayValidationError("start_time dan end_time wajib (HH:MM)")
    save_hours(conn, iso, start, end, day_type)


def create_draft(
    conn: sqlite3.Connection,
    iso: str,
    summary: str | None = None,
) -> dict[str, Any]:
    try:
        draft = orchestrator.finish_day(conn, iso, summary)
    except ValueError as e:
        raise DayValidationError(str(e)) from e
    label = STATUS_SKIPPED if draft.get("status") == "skipped" else STATUS_SAVED
    return {"ok": True, "status_label": label, "draft": draft, "live_sent": False}


def fill_day(
    conn: sqlite3.Connection,
    iso: str,
    mode: str,
    *,
    summary: str | None,
    credentials_present: bool,
) -> dict[str, Any]:
    """Save a local draft, then dry-run or live-fill. Missing creds stay on dry-run."""
    resolved = parse_fill_mode(mode)
    try:
        draft = orchestrator.finish_day(conn, iso, summary)
    except ValueError as e:
        raise DayValidationError(str(e)) from e

    if draft.get("status") == "skipped" or draft.get("skip_blok"):
        return {
            "ok": True,
            "date": iso,
            "status_label": STATUS_SKIPPED,
            "mode_requested": resolved,
            "live_sent": False,
            "credentials_present": credentials_present,
            "draft": draft,
            "worker": {"skipped": True, "reason": "frei"},
            "preview_url": None,
        }

    use_live = resolved == "live" and credentials_present
    live_error = None
    if use_live:
        try:
            worker = blok_worker.run_worker(conn, iso, dry_run=False, live=True)
            label = STATUS_LIVE_SENT
        except (RuntimeError, OSError) as e:
            # Draft is already committed. Keep a local HTML preview and do not claim a live send.
            worker = blok_worker.run_worker(conn, iso, dry_run=True, live=False)
            label = STATUS_SAVED_DRY_RUN
            live_error = str(e)
            use_live = False
    else:
        worker = blok_worker.run_worker(conn, iso, dry_run=True, live=False)
        label = STATUS_SKIPPED if worker.get("skipped") else STATUS_SAVED_DRY_RUN

    preview_url = None
    output = worker.get("output") if isinstance(worker, dict) else None
    if output:
        preview_url = f"/dashboard/blok-preview/{Path(output).name}"
    elif (blok_worker.OUTPUT_DIR / f"{iso}.html").is_file():
        preview_url = f"/dashboard/blok-preview/{iso}.html"

    public_worker = {
        "dry_run": bool(worker.get("dry_run")) if isinstance(worker, dict) else False,
        "skipped": bool(worker.get("skipped")) if isinstance(worker, dict) else False,
        "saved": worker.get("saved") if isinstance(worker, dict) else None,
        "reason": worker.get("reason") if isinstance(worker, dict) else None,
        "note": worker.get("note") if isinstance(worker, dict) else None,
        "preview_url": preview_url,
    }
    return {
        "ok": True,
        "date": iso,
        "status_label": label,
        "mode_requested": resolved,
        "live_sent": use_live and not public_worker["skipped"],
        "credentials_present": credentials_present,
        "fallback_dry_run": resolved == "live" and not use_live,
        "live_error": live_error,
        "draft": draft,
        "worker": public_worker,
        "preview_url": preview_url,
    }


def decode_image(image_base64: str) -> bytes:
    raw_text = (image_base64 or "").strip()
    if raw_text.startswith("data:") and "," in raw_text:
        raw_text = raw_text.split(",", 1)[1]
    try:
        raw = base64.b64decode(raw_text, validate=True)
    except Exception as e:
        raise DayValidationError(f"image_base64 tidak valid: {e}") from e
    if not raw:
        raise DayValidationError("gambar kosong")
    if len(raw) > MAX_PHOTO_BYTES:
        raise DayValidationError("Gambar terlalu besar (max 15 MB)")
    return raw


def _safe_filename(filename: str | None, ext: str) -> str:
    base = Path(filename or "foto").name
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")[:80] or "foto"
    if not base.lower().endswith(ext):
        stem = Path(base).stem or "foto"
        base = f"{stem}{ext}"
    return base


def save_photo(
    conn: sqlite3.Connection,
    iso: str,
    image_base64: str,
    *,
    mime_type: str | None,
    filename: str | None,
    caption: str | None,
    attachments_root: Path,
    repo_root: Path,
) -> dict[str, Any]:
    mime = (mime_type or "image/jpeg").split(";", 1)[0].strip().lower()
    ext = MIME_EXT.get(mime)
    if not ext:
        raise DayValidationError("mime_type harus jpeg, png, webp, atau gif")
    raw = decode_image(image_base64)
    day_dir = attachments_root / iso
    day_dir.mkdir(parents=True, exist_ok=True)
    name = _safe_filename(filename, ext)
    path = day_dir / name
    if path.exists():
        stem = path.stem
        suffix = path.suffix
        index = 2
        while path.exists():
            path = day_dir / f"{stem}-{index}{suffix}"
            index += 1
    path.write_bytes(raw)
    try:
        rel = str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        rel = str(path)
    attachment_id = db.add_attachment(
        conn,
        iso,
        rel,
        caption=(caption or "").strip() or None,
        kind="photo",
        vision_mode=None,
    )
    db.update_attachment_blok(conn, attachment_id, "pending")
    return {
        "ok": True,
        "id": attachment_id,
        "date": iso,
        "path": rel,
        "media_url": media_url_for(rel),
        "blok_status": "pending",
        "status_label": STATUS_UPLOAD_PENDING,
    }


def upload_photos_to_blok(
    conn: sqlite3.Connection,
    iso: str,
    attachment_ids: list[int] | None,
    *,
    credentials_present: bool,
    bind: bool = True,
) -> dict[str, Any]:
    """Live upload only when credentials already exist. Otherwise leave files pending."""
    if attachment_ids:
        rows = [db.get_attachment(conn, attachment_id) for attachment_id in attachment_ids]
        rows = [row for row in rows if row and row["date"] == iso]
    else:
        rows = db.attachments_for_date(conn, iso)
    if not rows:
        raise DayValidationError("Tidak ada foto untuk tanggal ini")

    if not credentials_present:
        results = []
        for row in rows:
            status = row["blok_status"]
            if status in ("uploaded", "bound"):
                results.append(
                    {
                        "attachment_id": row["id"],
                        "blok_status": status,
                        "skipped": True,
                    }
                )
                continue
            db.update_attachment_blok(conn, row["id"], "pending")
            results.append({"attachment_id": row["id"], "blok_status": "pending"})
        return {
            "ok": True,
            "date": iso,
            "live": False,
            "status_label": STATUS_UPLOAD_PENDING,
            "message": "tersimpan lokal, upload BLok menunggu kredensial",
            "results": results,
        }

    results = upload_attachments_for_date(conn, iso, [row["id"] for row in rows], bind=bind)
    uploaded = sum(1 for item in results if not item.get("error") and not item.get("skipped"))
    return {
        "ok": True,
        "date": iso,
        "live": True,
        "status_label": STATUS_LIVE_SENT if uploaded else STATUS_UPLOAD_PENDING,
        "uploaded": uploaded,
        "results": results,
    }
