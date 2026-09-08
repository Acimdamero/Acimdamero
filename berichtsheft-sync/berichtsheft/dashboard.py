"""Ops dashboard — health, live feed, editors for katalog / shifts / school."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from berichtsheft import catalog, db
from berichtsheft.ai_gemini import is_enabled as gemini_enabled
from berichtsheft.ai_vision import is_vision_enabled
from berichtsheft.config_loader import ROOT, load_config, load_dotenv
from berichtsheft.cursor_agent import is_available as cursor_available
from berichtsheft.seed import load_shifts

STATIC_DIR = Path(__file__).resolve().parent / "static" / "dashboard"
BLOK_DRY_RUN = ROOT / "output" / "blok_dry_run"
SHIFTS_SAMPLE = ROOT / "data" / "shifts_kw23_24.json"
ATTACHMENTS_DIR = ROOT / "data" / "attachments"

router = APIRouter(tags=["dashboard"])


class CatalogSaveBody(BaseModel):
    katalog: dict[str, Any]
    sync_db: bool = True
    write_md: bool = False
    export_legacy: bool = True


class ShiftBody(BaseModel):
    date: str
    day_type: str = "arbeit"
    start: Optional[str] = None
    end: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    segments: list[dict[str, Any]] = Field(default_factory=list)
    source: str = "dashboard"


class ShiftsJsonBody(BaseModel):
    data: dict[str, Any]
    import_to_db: bool = True


def _dashboard_token() -> str:
    load_dotenv()
    return os.environ.get("DASHBOARD_TOKEN", "").strip()


def require_dashboard_access(
    request: Request,
    x_dashboard_token: Optional[str] = Header(default=None),
    token: Optional[str] = Query(default=None),
) -> None:
    """If DASHBOARD_TOKEN set, require matching header/query. Else allow (local ops)."""
    expected = _dashboard_token()
    if not expected:
        return
    provided = (x_dashboard_token or token or "").strip()
    if provided != expected:
        raise HTTPException(401, "Dashboard token required (X-Dashboard-Token or ?token=)")


def _conn():
    conn = db.connect()
    db.init_schema(conn)
    return conn


def _row_to_dict(row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _attachment_exists(rel_path: str) -> bool:
    if not rel_path:
        return False
    p = (ROOT / rel_path).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError:
        return False
    return p.is_file()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _safe_under(base: Path, name: str) -> Path:
    """Resolve path under base; reject traversal."""
    target = (base / name).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError as e:
        raise HTTPException(400, "path tidak valid") from e
    return target


# ── Pages & static ──────────────────────────────────────────────────────────


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(_: None = Depends(require_dashboard_access)):
    index = STATIC_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(500, "dashboard static missing")
    return HTMLResponse(index.read_text(encoding="utf-8"))


@router.get("/dashboard/blok-preview/{filename}")
def blok_preview(filename: str, _: None = Depends(require_dashboard_access)):
    path = _safe_under(BLOK_DRY_RUN, filename)
    if not path.is_file():
        raise HTTPException(404, "dry-run file tidak ada")
    media = "text/html" if path.suffix == ".html" else "application/json"
    return FileResponse(path, media_type=media)


@router.get("/dashboard/media/{path:path}")
def media_file(path: str, _: None = Depends(require_dashboard_access)):
    """Serve attachment files under data/attachments (thumbnails)."""
    # Allow either "2026-06-05/foo.jpg" or full "data/attachments/..."
    rel = path
    if rel.startswith("data/attachments/"):
        file_path = _safe_under(ROOT, rel)
    else:
        file_path = _safe_under(ATTACHMENTS_DIR, rel)
    if not file_path.is_file():
        raise HTTPException(404, "file tidak ada")
    return FileResponse(file_path)


# ── Health / overview ───────────────────────────────────────────────────────


@router.get("/dashboard/api/health")
def dashboard_health(_: None = Depends(require_dashboard_access)):
    load_dotenv()
    tg_token = bool(os.environ.get("TELEGRAM_BOT_TOKEN", "").strip())
    wa_allowed = bool(os.environ.get("WHATSAPP_ALLOWED_NUMBER", "").strip())
    gemini_key = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    dash_token_set = bool(_dashboard_token())

    tg_chat = (ROOT / "data" / "telegram_chat_id.txt").is_file()
    wa_chat = (ROOT / "data" / "whatsapp_chat_id.txt").is_file()

    waha: dict[str, Any] = {"ok": False, "error": "not checked"}
    try:
        from berichtsheft.whatsapp_bot import check_waha

        waha = check_waha()
    except Exception as e:  # noqa: BLE001 — surface status only
        waha = {"ok": False, "error": str(e)}

    dry_runs = []
    if BLOK_DRY_RUN.is_dir():
        dry_runs = sorted(
            [p.name for p in BLOK_DRY_RUN.iterdir() if p.suffix in (".html", ".json")],
            reverse=True,
        )[:20]

    cfg = load_config()
    server = cfg.get("server") or {}

    return {
        "ok": True,
        "service": "berichtsheft-sync",
        "api": True,
        "gemini_key_present": gemini_key,
        "gemini_enabled": gemini_enabled(),
        "vision_enabled": is_vision_enabled(),
        "cursor_available": cursor_available(),
        "telegram_token_present": tg_token,
        "telegram_chat_id_saved": tg_chat,
        "whatsapp_allowlist_set": wa_allowed,
        "whatsapp_chat_id_saved": wa_chat,
        "waha": waha,
        "dashboard_token_required": dash_token_set,
        "blok_dry_run_files": dry_runs,
        "katalog_path": _rel(catalog.KATALOG_PATH),
        "db_path": str(Path(db.DEFAULT_DB).name),
        "server": {"host": server.get("host", "127.0.0.1"), "port": server.get("port", 8765)},
        "auth_note": (
            "DASHBOARD_TOKEN set — send X-Dashboard-Token"
            if dash_token_set
            else "DASHBOARD_TOKEN empty — open access (use localhost / private network only)"
        ),
    }


# ── Live feed ───────────────────────────────────────────────────────────────


@router.get("/dashboard/api/live")
def dashboard_live(
    limit: int = Query(default=25, ge=1, le=100),
    _: None = Depends(require_dashboard_access),
):
    conn = _conn()
    logs = [_row_to_dict(r) for r in db.recent_work_logs(conn, limit)]
    drafts = [_row_to_dict(r) for r in db.recent_drafts(conn, limit)]
    atts = []
    for r in db.recent_attachments(conn, limit):
        item = _row_to_dict(r)
        rel = item.get("path") or ""
        item["file_exists"] = _attachment_exists(rel)
        if item["file_exists"]:
            # URL under /dashboard/media/
            if rel.startswith("data/attachments/"):
                item["media_url"] = "/dashboard/media/" + rel[len("data/attachments/") :]
            else:
                item["media_url"] = f"/dashboard/media/{rel}"
        else:
            item["media_url"] = None
        atts.append(item)
    conn.close()
    return {"ok": True, "work_logs": logs, "drafts": drafts, "attachments": atts}


# ── Catalog editor ──────────────────────────────────────────────────────────


@router.get("/dashboard/api/catalog")
def dashboard_get_catalog(_: None = Depends(require_dashboard_access)):
    data = catalog.load_katalog()
    return {"ok": True, "katalog": data, "path": _rel(catalog.KATALOG_PATH)}


@router.put("/dashboard/api/catalog")
def dashboard_put_catalog(
    body: CatalogSaveBody,
    _: None = Depends(require_dashboard_access),
):
    try:
        path = catalog.save_katalog(body.katalog)
    except (ValueError, TypeError, OSError) as e:
        raise HTTPException(400, str(e)) from e

    stats = None
    if body.sync_db:
        conn = _conn()
        stats = catalog.sync_to_db(conn, body.katalog)
        conn.close()
    if body.export_legacy:
        catalog.export_legacy_files(body.katalog)
    md_path = None
    if body.write_md:
        md_path = _rel(catalog.write_docs_markdown(body.katalog))

    return {
        "ok": True,
        "path": _rel(path),
        "sync": stats,
        "docs": md_path,
    }


# ── Shifts / jadwal ─────────────────────────────────────────────────────────


@router.get("/dashboard/api/shifts")
def dashboard_list_shifts(
    limit: int = Query(default=100, ge=1, le=500),
    _: None = Depends(require_dashboard_access),
):
    conn = _conn()
    rows = []
    for r in db.list_shifts(conn, limit):
        item = _row_to_dict(r)
        try:
            item["tags"] = json.loads(item.pop("tags_json") or "[]")
        except json.JSONDecodeError:
            item["tags"] = []
        try:
            item["segments"] = json.loads(item.pop("segments_json") or "[]")
        except json.JSONDecodeError:
            item["segments"] = []
        rows.append(item)
    conn.close()
    return {"ok": True, "shifts": rows}


@router.put("/dashboard/api/shifts")
def dashboard_upsert_shift(
    body: ShiftBody,
    _: None = Depends(require_dashboard_access),
):
    conn = _conn()
    db.upsert_shift(
        conn,
        {
            "date": body.date,
            "day_type": body.day_type,
            "start": body.start,
            "end": body.end,
            "tags": body.tags,
            "segments": body.segments,
            "source": body.source,
        },
    )
    conn.commit()
    conn.close()
    return {"ok": True, "date": body.date}


@router.delete("/dashboard/api/shifts/{date}")
def dashboard_delete_shift(date: str, _: None = Depends(require_dashboard_access)):
    conn = _conn()
    ok = db.delete_shift(conn, date)
    conn.close()
    if not ok:
        raise HTTPException(404, f"Shift tidak ada: {date}")
    return {"ok": True, "deleted": date}


@router.get("/dashboard/api/shifts/json")
def dashboard_get_shifts_json(_: None = Depends(require_dashboard_access)):
    if not SHIFTS_SAMPLE.is_file():
        raise HTTPException(404, f"{SHIFTS_SAMPLE.name} tidak ada")
    data = json.loads(SHIFTS_SAMPLE.read_text(encoding="utf-8"))
    return {
        "ok": True,
        "path": _rel(SHIFTS_SAMPLE),
        "data": data,
    }


@router.put("/dashboard/api/shifts/json")
def dashboard_put_shifts_json(
    body: ShiftsJsonBody,
    _: None = Depends(require_dashboard_access),
):
    if "shifts" not in body.data or not isinstance(body.data["shifts"], list):
        raise HTTPException(400, "JSON harus punya key 'shifts' (list)")
    SHIFTS_SAMPLE.write_text(
        json.dumps(body.data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    imported = 0
    if body.import_to_db:
        conn = _conn()
        imported = load_shifts(conn, SHIFTS_SAMPLE)
        conn.close()
    return {
        "ok": True,
        "path": _rel(SHIFTS_SAMPLE),
        "imported": imported,
    }


# ── School / templates ──────────────────────────────────────────────────────


@router.get("/dashboard/api/school")
def dashboard_school(_: None = Depends(require_dashboard_access)):
    data = catalog.load_katalog()
    school = [
        a
        for a in data.get("abteilungen", [])
        if (a.get("blok_name") or "").lower() in ("schule", "school")
        or any(
            (c.get("code") or "").lower() == "schule" for c in (a.get("codes") or [])
        )
    ]
    # also pull templates_hotelfach for Schule codes
    templates_path = catalog.TEMPLATES_PATH
    templates = []
    if templates_path.is_file():
        raw = json.loads(templates_path.read_text(encoding="utf-8"))
        templates = [
            t
            for t in raw.get("templates", [])
            if (t.get("code") or "").lower() == "schule"
            or (t.get("department") or "").lower() in ("schule", "berufsschule")
        ]
    return {
        "ok": True,
        "abteilungen": school,
        "templates_schule": templates,
        "katalog_path": _rel(catalog.KATALOG_PATH),
        "templates_path": _rel(templates_path),
        "hint": "Edit materi sekolah lewat panel Katalog (Abteilung Schule) lalu Save + Sync DB.",
    }


# ── BLok dry-run ────────────────────────────────────────────────────────────


@router.get("/dashboard/api/blok")
def dashboard_blok(_: None = Depends(require_dashboard_access)):
    files = []
    if BLOK_DRY_RUN.is_dir():
        for p in sorted(BLOK_DRY_RUN.iterdir(), reverse=True):
            if p.suffix not in (".html", ".json"):
                continue
            files.append(
                {
                    "name": p.name,
                    "size": p.stat().st_size,
                    "preview_url": f"/dashboard/blok-preview/{p.name}",
                    "kind": p.suffix.lstrip("."),
                }
            )
    keychain = shutil.which("security") is not None  # macOS Keychain CLI
    return {
        "ok": True,
        "mode": "dry-run / offline",
        "live_available": False,
        "keychain_available": keychain,
        "blok_url": "https://www.online-ausbildungsnachweis.de",
        "docs": [
            "docs/BLok_LIVE.md",
            "docs/BLok_AUTOMATION.md",
            "docs/BLok_WOCHE.md",
        ],
        "dry_run_dir": "output/blok_dry_run/",
        "files": files,
        "note": (
            "Live BLok login butuh Keychain (Mac). Di cloud/VM ini panel menampilkan "
            "hasil dry-run terakhir saja — tidak scrape kredensial."
        ),
    }


# ── Bots ────────────────────────────────────────────────────────────────────


@router.get("/dashboard/api/bots")
def dashboard_bots(_: None = Depends(require_dashboard_access)):
    load_dotenv()
    from berichtsheft.telegram_bot import BOT_COMMANDS, MENU_ACTIONS

    tg_token = bool(os.environ.get("TELEGRAM_BOT_TOKEN", "").strip())
    tg_chat_file = ROOT / "data" / "telegram_chat_id.txt"
    tg_chat_id = None
    if tg_chat_file.is_file():
        tg_chat_id = tg_chat_file.read_text(encoding="utf-8").strip() or None

    wa_chat_file = ROOT / "data" / "whatsapp_chat_id.txt"
    wa_chat_id = None
    if wa_chat_file.is_file():
        wa_chat_id = wa_chat_file.read_text(encoding="utf-8").strip() or None

    waha: dict[str, Any] = {"ok": False}
    try:
        from berichtsheft.whatsapp_bot import check_waha

        waha = check_waha()
    except Exception as e:  # noqa: BLE001
        waha = {"ok": False, "error": str(e)}

    menu_labels = list(MENU_ACTIONS.keys())

    return {
        "ok": True,
        "telegram": {
            "token_present": tg_token,
            "chat_id_saved": tg_chat_id is not None,
            "chat_id": tg_chat_id,
            "commands": BOT_COMMANDS,
            "menu_buttons": menu_labels,
            "open_hint": "Buka Telegram → cari bot Anda → /start",
            "docs": "docs/TELEGRAM.md",
        },
        "whatsapp": {
            "allowlist_set": bool(os.environ.get("WHATSAPP_ALLOWED_NUMBER", "").strip()),
            "chat_id_saved": wa_chat_id is not None,
            "chat_id": wa_chat_id,
            "waha": waha,
            "open_hint": "WAHA dashboard biasanya http://127.0.0.1:3000 — lihat docs/WHATSAPP.md",
            "docs": "docs/WHATSAPP.md",
        },
    }


def mount_dashboard(app) -> None:
    """Attach router + static assets to FastAPI app."""
    if STATIC_DIR.is_dir():
        app.mount(
            "/dashboard/static",
            StaticFiles(directory=str(STATIC_DIR)),
            name="dashboard-static",
        )
    app.include_router(router)
