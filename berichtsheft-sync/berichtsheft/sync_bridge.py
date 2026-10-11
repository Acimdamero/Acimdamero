"""Cloud ↔ Mac sync bridge — export/import shifts, logs, drafts, katalog.

Auth: SYNC_TOKEN or DASHBOARD_TOKEN (never expose DB without a token).
Recommended MVP: Mac API behind Cloudflare Tunnel / Tailscale; Cloud points
BERICHTSHEFT_API (or sync remote URL) at that host. See docs/CLOUD_LOCAL_BRIDGE.md.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

from berichtsheft import catalog, db
from berichtsheft.config_loader import ROOT, load_dotenv

SCHEMA_VERSION = 1
SYNC_CONFIG_PATH = ROOT / "data" / "sync_config.json"
KATALOG_FILES = (
    "katalog_abteilung.json",
    "areas_hotel.json",
    "templates_hotelfach.json",
    "shifts_kw23_24.json",
    "shifts_edtime_kw22_24.json",
    "blok_mapping.yaml",
)
MAX_ATTACHMENT_BYTES = 2 * 1024 * 1024  # 2 MiB per file in payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sync_token() -> str:
    """Prefer SYNC_TOKEN; fall back to DASHBOARD_TOKEN."""
    load_dotenv()
    return (
        os.environ.get("SYNC_TOKEN", "").strip()
        or os.environ.get("DASHBOARD_TOKEN", "").strip()
    )


def load_sync_config() -> dict[str, Any]:
    if not SYNC_CONFIG_PATH.is_file():
        return {
            "remote_api_url": os.environ.get("BERICHTSHEFT_REMOTE_API", "").strip()
            or os.environ.get("BERICHTSHEFT_API", "").strip()
            or "",
            "last_pull_at": None,
            "last_push_at": None,
            "last_error": None,
            "last_counts": {},
        }
    try:
        data = json.loads(SYNC_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("remote_api_url", "")
    data.setdefault("last_pull_at", None)
    data.setdefault("last_push_at", None)
    data.setdefault("last_error", None)
    data.setdefault("last_counts", {})
    return data


def save_sync_config(cfg: dict[str, Any]) -> Path:
    SYNC_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # never persist tokens
    clean = {
        "remote_api_url": (cfg.get("remote_api_url") or "").strip().rstrip("/"),
        "last_pull_at": cfg.get("last_pull_at"),
        "last_push_at": cfg.get("last_push_at"),
        "last_error": cfg.get("last_error"),
        "last_counts": cfg.get("last_counts") or {},
    }
    SYNC_CONFIG_PATH.write_text(
        json.dumps(clean, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return SYNC_CONFIG_PATH


def _row_dict(row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _export_katalog_files() -> dict[str, Any]:
    out: dict[str, Any] = {}
    data_dir = ROOT / "data"
    for name in KATALOG_FILES:
        path = data_dir / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if name.endswith(".json"):
            try:
                out[name] = json.loads(text)
            except json.JSONDecodeError:
                out[name] = {"_raw": text}
        else:
            out[name] = {"_raw": text}
    return out


def _export_attachments(
    conn,
    *,
    include_files: bool = False,
    limit: int = 200,
) -> list[dict[str, Any]]:
    rows = db.recent_attachments(conn, limit)
    items: list[dict[str, Any]] = []
    for row in rows:
        item = _row_dict(row)
        rel = item.get("path") or ""
        item["file_exists"] = False
        item["content_base64"] = None
        if rel:
            path = (ROOT / rel).resolve()
            try:
                path.relative_to(ROOT.resolve())
            except ValueError:
                items.append(item)
                continue
            if path.is_file():
                item["file_exists"] = True
                if include_files and path.stat().st_size <= MAX_ATTACHMENT_BYTES:
                    item["content_base64"] = base64.b64encode(path.read_bytes()).decode(
                        "ascii"
                    )
                    item["content_size"] = path.stat().st_size
        items.append(item)
    return items


def build_export_payload(
    conn,
    *,
    include: Optional[list[str]] = None,
    include_attachment_files: bool = False,
) -> dict[str, Any]:
    """Build a JSON-serializable sync snapshot from local SQLite + data/."""
    wanted = set(include or ["shifts", "work_logs", "drafts", "approvals", "katalog", "attachments"])
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "exported_at": _utc_now(),
        "source": "berichtsheft-sync",
        "counts": {},
        "data": {},
    }

    if "shifts" in wanted:
        shifts = [_row_dict(r) for r in db.list_shifts(conn, limit=5000)]
        for s in shifts:
            if isinstance(s.get("tags_json"), str):
                try:
                    s["tags"] = json.loads(s["tags_json"] or "[]")
                except json.JSONDecodeError:
                    s["tags"] = []
            if isinstance(s.get("segments_json"), str):
                try:
                    s["segments"] = json.loads(s["segments_json"] or "[]")
                except json.JSONDecodeError:
                    s["segments"] = []
        payload["data"]["shifts"] = shifts
        payload["counts"]["shifts"] = len(shifts)

    if "work_logs" in wanted:
        logs = [
            _row_dict(r)
            for r in conn.execute(
                "SELECT * FROM work_logs ORDER BY id ASC"
            ).fetchall()
        ]
        payload["data"]["work_logs"] = logs
        payload["counts"]["work_logs"] = len(logs)

    if "drafts" in wanted:
        drafts = [
            _row_dict(r)
            for r in conn.execute(
                "SELECT * FROM draft_entries ORDER BY date ASC"
            ).fetchall()
        ]
        payload["data"]["drafts"] = drafts
        payload["counts"]["drafts"] = len(drafts)

    if "approvals" in wanted:
        approvals = [
            _row_dict(r)
            for r in conn.execute("SELECT * FROM approvals ORDER BY date ASC").fetchall()
        ]
        payload["data"]["approvals"] = approvals
        payload["counts"]["approvals"] = len(approvals)

    if "katalog" in wanted:
        files = _export_katalog_files()
        payload["data"]["katalog_files"] = files
        payload["counts"]["katalog_files"] = len(files)

    if "attachments" in wanted:
        atts = _export_attachments(
            conn, include_files=include_attachment_files, limit=500
        )
        payload["data"]["attachments"] = atts
        payload["counts"]["attachments"] = len(atts)

    return payload


def apply_import_payload(
    conn,
    payload: dict[str, Any],
    *,
    mode: str = "merge",
) -> dict[str, Any]:
    """Apply a sync payload into local DB + data/ files.

    mode=merge: upsert by natural keys; skip duplicate work_logs.
    mode=replace: for shifts/drafts/approvals clear matching dates then insert;
      work_logs still de-duped by (date, content, source, created_at).
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        raise ValueError("payload.data must be an object")

    stats: dict[str, Any] = {
        "mode": mode,
        "shifts_upserted": 0,
        "work_logs_added": 0,
        "work_logs_skipped": 0,
        "drafts_upserted": 0,
        "approvals_upserted": 0,
        "katalog_files_written": 0,
        "attachments_restored": 0,
        "attachments_meta": 0,
    }

    db.init_schema(conn)

    for row in data.get("shifts") or []:
        if not row.get("date"):
            continue
        tags = row.get("tags")
        if tags is None and row.get("tags_json"):
            try:
                tags = json.loads(row["tags_json"])
            except (TypeError, json.JSONDecodeError):
                tags = []
        segments = row.get("segments")
        if segments is None and row.get("segments_json"):
            try:
                segments = json.loads(row["segments_json"])
            except (TypeError, json.JSONDecodeError):
                segments = []
        db.upsert_shift(
            conn,
            {
                "date": row["date"],
                "day_type": row.get("day_type") or "arbeit",
                "start": row.get("start_time") or row.get("start"),
                "end": row.get("end_time") or row.get("end"),
                "tags": tags or [],
                "segments": segments or [],
                "source": row.get("source") or "sync",
            },
        )
        stats["shifts_upserted"] += 1

    existing_logs = {
        (r["date"], r["content"], r["source"] or "", r["created_at"] or "")
        for r in conn.execute(
            "SELECT date, content, source, created_at FROM work_logs"
        ).fetchall()
    }
    for row in data.get("work_logs") or []:
        key = (
            row.get("date") or "",
            row.get("content") or "",
            row.get("source") or "",
            row.get("created_at") or "",
        )
        if not key[0] or not key[1]:
            continue
        if key in existing_logs:
            stats["work_logs_skipped"] += 1
            continue
        if row.get("created_at"):
            conn.execute(
                """
                INSERT INTO work_logs (date, content, source, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (key[0], key[1], key[2] or "sync", key[3]),
            )
        else:
            db.add_work_log(conn, key[0], key[1], source=key[2] or "sync")
        existing_logs.add(key)
        stats["work_logs_added"] += 1

    for row in data.get("drafts") or []:
        if not row.get("date"):
            continue
        db.save_draft(
            conn,
            row["date"],
            row.get("hours"),
            row.get("ort") or "Betrieb",
            row.get("lernfeld"),
            row.get("taetigkeiten") or "",
            status=row.get("status") or "draft",
        )
        stats["drafts_upserted"] += 1

    for row in data.get("approvals") or []:
        if not row.get("date"):
            continue
        db.set_approval(
            conn,
            row["date"],
            row.get("status") or "pending",
            note=row.get("note"),
        )
        stats["approvals_upserted"] += 1

    katalog_files = data.get("katalog_files") or {}
    if isinstance(katalog_files, dict):
        data_dir = ROOT / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        for name, content in katalog_files.items():
            safe = Path(name).name
            if safe not in KATALOG_FILES:
                continue
            path = data_dir / safe
            if isinstance(content, dict) and "_raw" in content and len(content) == 1:
                path.write_text(str(content["_raw"]), encoding="utf-8")
            elif isinstance(content, (dict, list)):
                path.write_text(
                    json.dumps(content, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            else:
                path.write_text(str(content), encoding="utf-8")
            stats["katalog_files_written"] += 1
        if "katalog_abteilung.json" in katalog_files:
            try:
                catalog.sync_to_db(conn)
                catalog.export_legacy_files()
            except Exception:  # noqa: BLE001 — sync best-effort after file write
                pass

    for row in data.get("attachments") or []:
        rel = row.get("path") or ""
        if not rel or ".." in rel:
            continue
        path = (ROOT / rel).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError:
            continue
        b64 = row.get("content_base64")
        if b64:
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                path.write_bytes(base64.b64decode(b64))
                stats["attachments_restored"] += 1
            except Exception:  # noqa: BLE001
                continue
        # metadata only if no matching row
        if row.get("date") and rel:
            existing = conn.execute(
                "SELECT id FROM attachments WHERE date = ? AND path = ?",
                (row["date"], rel),
            ).fetchone()
            if not existing:
                db.add_attachment(
                    conn,
                    row["date"],
                    rel,
                    caption=row.get("caption"),
                    kind=row.get("kind") or "photo",
                    vision_mode=row.get("vision_mode"),
                )
                stats["attachments_meta"] += 1

    conn.commit()
    return stats


def status_summary(conn) -> dict[str, Any]:
    cfg = load_sync_config()
    load_dotenv()
    token_set = bool(sync_token())
    counts = {
        "shifts": conn.execute("SELECT COUNT(*) FROM shifts").fetchone()[0],
        "work_logs": conn.execute("SELECT COUNT(*) FROM work_logs").fetchone()[0],
        "drafts": conn.execute("SELECT COUNT(*) FROM draft_entries").fetchone()[0],
        "approvals": conn.execute("SELECT COUNT(*) FROM approvals").fetchone()[0],
        "attachments": conn.execute("SELECT COUNT(*) FROM attachments").fetchone()[0],
    }
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "token_required": token_set,
        "token_configured": token_set,
        "remote_api_url": cfg.get("remote_api_url") or "",
        "last_pull_at": cfg.get("last_pull_at"),
        "last_push_at": cfg.get("last_push_at"),
        "last_error": cfg.get("last_error"),
        "last_counts": cfg.get("last_counts") or {},
        "local_counts": counts,
        "db_path": str(Path(db.DEFAULT_DB).name),
        "docs": "docs/CLOUD_LOCAL_BRIDGE.md",
        "mode_a_hint": (
            "Mac: expose serve via cloudflared/Tailscale + DASHBOARD_TOKEN. "
            "Cloud: set remote_api_url / BERICHTSHEFT_API to that URL."
        ),
    }


def _auth_headers(token: str) -> dict[str, str]:
    t = token.strip()
    return {
        "Authorization": f"Bearer {t}",
        "X-Dashboard-Token": t,
        "X-Sync-Token": t,
        "Content-Type": "application/json",
    }


def remote_pull(
    url: str,
    token: str,
    *,
    include_attachment_files: bool = False,
    timeout: float = 60.0,
) -> dict[str, Any]:
    base = url.rstrip("/")
    params = {}
    if include_attachment_files:
        params["include_files"] = "1"
    with httpx.Client(timeout=timeout) as client:
        r = client.get(
            f"{base}/sync/pull",
            headers=_auth_headers(token),
            params=params,
        )
        r.raise_for_status()
        return r.json()


def remote_push(
    url: str,
    token: str,
    payload: dict[str, Any],
    *,
    mode: str = "merge",
    timeout: float = 60.0,
) -> dict[str, Any]:
    base = url.rstrip("/")
    body = {**payload, "mode": mode}
    with httpx.Client(timeout=timeout) as client:
        r = client.post(
            f"{base}/sync/push",
            headers=_auth_headers(token),
            json=body,
        )
        r.raise_for_status()
        return r.json()


def cli_sync_pull(
    url: str,
    token: str,
    *,
    include_attachment_files: bool = False,
    apply: bool = True,
) -> dict[str, Any]:
    payload = remote_pull(
        url, token, include_attachment_files=include_attachment_files
    )
    result: dict[str, Any] = {"pulled": True, "remote_counts": payload.get("counts")}
    if apply:
        conn = db.connect()
        db.init_schema(conn)
        stats = apply_import_payload(conn, payload, mode="merge")
        conn.close()
        result["applied"] = stats
        cfg = load_sync_config()
        cfg["remote_api_url"] = url.rstrip("/")
        cfg["last_pull_at"] = _utc_now()
        cfg["last_error"] = None
        cfg["last_counts"] = payload.get("counts") or {}
        save_sync_config(cfg)
    return result


def cli_sync_push(
    url: str,
    token: str,
    *,
    include_attachment_files: bool = False,
    mode: str = "merge",
) -> dict[str, Any]:
    conn = db.connect()
    db.init_schema(conn)
    payload = build_export_payload(
        conn, include_attachment_files=include_attachment_files
    )
    conn.close()
    remote = remote_push(url, token, payload, mode=mode)
    cfg = load_sync_config()
    cfg["remote_api_url"] = url.rstrip("/")
    cfg["last_push_at"] = _utc_now()
    cfg["last_error"] = None
    cfg["last_counts"] = payload.get("counts") or {}
    save_sync_config(cfg)
    return {"pushed": True, "local_counts": payload.get("counts"), "remote": remote}
