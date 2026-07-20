"""FastAPI — hooks for Telegram bot and health checks."""

from __future__ import annotations

import base64
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from berichtsheft import catalog, db, orchestrator
from berichtsheft.ai_gemini import is_enabled as gemini_enabled
from berichtsheft.ai_vision import analyze_image, is_vision_enabled
from berichtsheft.blok_gaps import format_telegram_report, scan_weeks
from berichtsheft.blok_upload import upload_attachments_for_date
from berichtsheft.blok_worker import run_worker
from berichtsheft.config_loader import ROOT, load_config
from berichtsheft.cursor_agent import is_available as cursor_available, run_agent_prompt

app = FastAPI(title="Berichtsheft-Sync API", version="0.3.0")

ATTACHMENTS_DIR = ROOT / "data" / "attachments"


class LogBody(BaseModel):
    text: str
    date: Optional[str] = None


class FinishBody(BaseModel):
    summary: Optional[str] = None
    date: Optional[str] = None
    fill_blok: Optional[bool] = None
    live_blok: Optional[bool] = None


class CorrectBody(BaseModel):
    text: str
    date: Optional[str] = None


class VisionBody(BaseModel):
    image_base64: str
    caption: Optional[str] = None
    mode: Optional[str] = None
    date: Optional[str] = None
    mime_type: Optional[str] = "image/jpeg"


class AiBody(BaseModel):
    text: str


class UploadBlokBody(BaseModel):
    attachment_ids: Optional[list[int]] = None
    date: Optional[str] = None
    bind: bool = True


class WeekScanBody(BaseModel):
    date: Optional[str] = None
    offsets: Optional[list[int]] = None


def _conn():
    conn = db.connect()
    db.init_schema(conn)
    return conn


@app.get("/health")
def health():
    from berichtsheft.ai_vision import is_vision_enabled

    return {
        "ok": True,
        "service": "berichtsheft-sync",
        "gemini": gemini_enabled(),
        "vision": is_vision_enabled(),
        "cursor": cursor_available(),
    }


@app.get("/catalog")
def get_catalog(abteilung: Optional[str] = None, code: Optional[str] = None):
    """Katalog kegiatan per Abteilung (dari data/katalog_abteilung.json)."""
    data = catalog.load_katalog()
    if code:
        for item in catalog.iter_codes(data):
            aliases = item.get("aliases") or []
            if item["code"] == code or code in aliases:
                return {"ok": True, "item": item}
        raise HTTPException(404, f"Code tidak ditemukan: {code}")
    if abteilung:
        needle = abteilung.strip().lower()
        matched = [
            a
            for a in data.get("abteilungen", [])
            if (a.get("blok_name") or "").lower() == needle
            or needle in (a.get("description_de") or "").lower()
        ]
        if not matched:
            raise HTTPException(404, f"Abteilung tidak ditemukan: {abteilung}")
        return {"ok": True, "abteilungen": matched}
    return {"ok": True, "katalog": data}


@app.post("/log")
def post_log(body: LogBody):
    iso = body.date or orchestrator.today_iso()
    conn = _conn()
    lid = db.add_work_log(conn, iso, body.text, source="api")
    conn.close()
    return {"ok": True, "id": lid, "date": iso}


@app.post("/vision/analyze")
def post_vision_analyze(body: VisionBody):
    from berichtsheft.ai_vision import is_vision_enabled

    if not is_vision_enabled():
        raise HTTPException(
            503,
            "Vision tidak aktif. Set GEMINI_API_KEY dan AI_VISION_ENABLED=true di .env",
        )

    iso = body.date or orchestrator.today_iso()
    try:
        raw = base64.b64decode(body.image_base64, validate=True)
    except Exception as e:
        raise HTTPException(400, f"image_base64 tidak valid: {e}") from e

    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(400, "Gambar terlalu besar (max 15 MB)")

    mime = body.mime_type or "image/jpeg"
    text, used_ai, mode_used = analyze_image(
        raw, mime_type=mime, caption=body.caption, mode=body.mode
    )

    day_dir = ATTACHMENTS_DIR / iso
    day_dir.mkdir(parents=True, exist_ok=True)
    ext = ".jpg"
    if "png" in mime:
        ext = ".png"
    elif "webp" in mime:
        ext = ".webp"
    fname = f"{iso}_{len(list(day_dir.glob('*')))}{ext}"
    fpath = day_dir / fname
    fpath.write_bytes(raw)

    conn = _conn()
    att_id = db.add_attachment(
        conn,
        iso,
        str(fpath.relative_to(ROOT)),
        caption=body.caption,
        kind="photo",
        vision_mode=mode_used,
    )

    log_id = None
    if mode_used != "edtime" and text and used_ai:
        prefix = f"[Vision/{mode_used}] "
        log_id = db.add_work_log(conn, iso, prefix + text, source="vision")
    conn.close()

    return {
        "ok": True,
        "date": iso,
        "mode": mode_used,
        "text": text,
        "used_ai": used_ai,
        "attachment_id": att_id,
        "attachment_path": str(fpath.relative_to(ROOT)),
        "log_id": log_id,
        "hint_edtime": (
            "Mode edtime: salin JSON ke data/shifts_….json lalu import di Mac."
            if mode_used == "edtime"
            else None
        ),
    }


@app.post("/ai")
def post_ai(body: AiBody):
    if not body.text.strip():
        raise HTTPException(400, "text kosong")
    if not cursor_available():
        raise HTTPException(
            503,
            "Cursor SDK tidak siap. Set CURSOR_API_KEY, jalankan npm install, "
            "lihat docs/FASE1.md",
        )
    result = run_agent_prompt(body.text.strip(), timeout_sec=300)
    if not result.get("ok"):
        raise HTTPException(502, result.get("error", "Cursor agent gagal"))
    return {"ok": True, **result}


@app.post("/finish")
def post_finish(body: FinishBody):
    iso = body.date or orchestrator.today_iso()
    conn = _conn()
    try:
        draft = orchestrator.finish_day(conn, iso, body.summary)
    except ValueError as e:
        conn.close()
        raise HTTPException(400, str(e)) from e

    cfg = load_config()
    orch = cfg.get("orchestrator") or {}
    auto = body.fill_blok
    if auto is None:
        auto = orch.get("auto_fill_blok_after_finish", True)

    live = body.live_blok
    if live is None:
        live = orch.get("live_blok_after_finish", False)
        if orch.get("require_ok_before_submit", False):
            live = False  # /selesai = dry-run; live hanya lewat /approve

    worker_result = None
    if auto and draft.get("status") != "skipped":
        worker_result = run_worker(conn, iso, dry_run=not live, live=live)

    preview = orchestrator_finish_preview(draft)
    conn.close()
    return {
        "ok": True,
        "draft": draft,
        "preview": preview,
        "worker": worker_result,
        "ai_polish": draft.get("ai_polish", False),
    }


@app.post("/approve")
def post_approve(date: Optional[str] = None, fill_blok: Optional[bool] = None):
    iso = date or orchestrator.today_iso()
    conn = _conn()
    try:
        result = orchestrator.approve_day(conn, iso)
    except ValueError as e:
        conn.close()
        raise HTTPException(400, str(e)) from e

    cfg = load_config()
    orch = cfg.get("orchestrator") or {}
    should_fill = fill_blok
    if should_fill is None and orch.get("require_ok_before_submit", False):
        should_fill = orch.get("auto_fill_blok_after_finish", True)

    worker_result = None
    if should_fill:
        live = orch.get("live_blok_after_finish", False)
        worker_result = run_worker(conn, iso, dry_run=not live, live=live)

    conn.close()
    return {"ok": True, **result, "worker": worker_result}


@app.post("/correct")
def post_correct(body: CorrectBody):
    iso = body.date or orchestrator.today_iso()
    conn = _conn()
    try:
        result = orchestrator.apply_correction(conn, iso, body.text)
    except ValueError as e:
        conn.close()
        raise HTTPException(400, str(e)) from e
    conn.close()
    return {"ok": True, "preview": orchestrator_finish_preview(result)}


@app.get("/attachments")
def get_attachments(date_str: Optional[str] = None):
    iso = date_str or orchestrator.today_iso()
    conn = _conn()
    rows = db.attachments_for_date(conn, iso)
    conn.close()
    return {
        "date": iso,
        "attachments": [
            {
                "id": r["id"],
                "path": r["path"],
                "caption": r["caption"],
                "vision_mode": r["vision_mode"],
                "blok_status": r["blok_status"],
                "blok_filename": r["blok_filename"],
                "created_at": r["created_at"],
            }
            for r in rows
        ],
    }


@app.post("/attachments/upload-blok")
def post_upload_blok(body: UploadBlokBody):
    iso = body.date or orchestrator.today_iso()
    conn = _conn()
    try:
        results = upload_attachments_for_date(
            conn,
            iso,
            body.attachment_ids,
            bind=body.bind,
        )
    except (RuntimeError, FileNotFoundError, ValueError) as e:
        conn.close()
        raise HTTPException(400, str(e)) from e
    conn.close()
    ok = sum(1 for r in results if not r.get("error") and not r.get("skipped"))
    return {"ok": True, "date": iso, "results": results, "uploaded": ok}


@app.get("/audit/weeks")
def get_audit_weeks(date_str: Optional[str] = None, offsets: str = "-1,0,1"):
    iso = date_str or orchestrator.today_iso()
    center = date.fromisoformat(iso)
    try:
        off = tuple(int(x.strip()) for x in offsets.split(",") if x.strip())
    except ValueError as e:
        raise HTTPException(400, "offsets harus angka dipisah koma") from e
    conn = _conn()
    try:
        scan = scan_weeks(conn, center, offsets=off or (-1, 0, 1))
    except RuntimeError as e:
        conn.close()
        raise HTTPException(503, str(e)) from e
    conn.close()
    return {
        "ok": True,
        "preview": format_telegram_report(scan),
        "report": scan,
    }


@app.post("/audit/run")
def post_audit_run(from_date: str, to_date: str):
    from berichtsheft.blok_audit import audit_range
    from berichtsheft.blok_gaps import analyze_week_gaps

    try:
        report = audit_range(
            date.fromisoformat(from_date),
            date.fromisoformat(to_date),
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e

    conn = _conn()
    gap_weeks = []
    for week in report.get("weeks") or []:
        gap_weeks.append(analyze_week_gaps(conn, week))
    conn.close()
    report["gap_analysis"] = gap_weeks
    return {"ok": True, "report": report, "preview": _format_full_audit(report, gap_weeks)}


def _format_full_audit(report: dict, gaps: list) -> str:
    lines = [
        f"📋 Audit BLok {report.get('range', {})}",
        f"Minggu: {report.get('summary', {}).get('weeks_scanned', 0)}",
        "",
    ]
    for g in gaps:
        s = g.get("summary") or {}
        if s.get("issue_count", 0):
            lines.append(f"KW {g.get('week_start')}: {s['issue_count']} isu")
            for issue in g.get("issues", [])[:5]:
                if issue.get("severity") in ("high", "medium"):
                    lines.append(f"  • {issue['message']}")
    if len(lines) <= 4:
        lines.append("✅ Tidak ada isu kritis")
    return "\n".join(lines)[:4000]


@app.get("/status")
def get_status(date_str: Optional[str] = None):
    iso = date_str or orchestrator.today_iso()
    conn = _conn()
    shift = db.get_shift(conn, iso)
    logs = db.work_logs_for_date(conn, iso)
    draft = db.get_draft(conn, iso)
    approval = db.get_approval(conn, iso)
    attachments = db.attachments_for_date(conn, iso)
    conn.close()
    return {
        "date": iso,
        "has_shift": shift is not None,
        "log_count": len(logs),
        "attachment_count": len(attachments),
        "draft_status": draft["status"] if draft else None,
        "approval": approval["status"] if approval else None,
    }


def orchestrator_finish_preview(draft: dict) -> str:
    lines = [
        f"📅 {draft['date']} ({draft.get('weekday', '')})",
        f"Ort: {draft.get('ort')}",
    ]
    if draft.get("hours"):
        lines.append(f"Zeit: {draft['hours']}")
    if draft.get("skip_blok"):
        lines.append("⚠ Hari libur — tidak diisi BLok")
    else:
        text = draft.get("taetigkeiten", "")
        short = text[:500] + ("…" if len(text) > 500 else "")
        lines.append(f"\n{short}")
        if draft.get("ai_polish"):
            lines.append("✨ Text mit KI (Gemini) verfeinert")
        lines.append("\n/ok = setuju")
        lines.append("/ubah formeller auf Deutsch … (satu pesan)")
    return "\n".join(lines)
