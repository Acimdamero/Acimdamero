"""BLok web worker — dry-run writes HTML; live uses Playwright + Keychain."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from berichtsheft import credentials, db
from berichtsheft.blok_fields import apply_day_fields
from berichtsheft.blok_hours import DEFAULT_STUNDEN, stunden_for_blok
from berichtsheft.blok_nav import go_to_week_containing_with_fallback
from berichtsheft.blok_status import live_fill_allowed
from berichtsheft.config_loader import ROOT, load_config

OUTPUT_DIR = ROOT / "output" / "blok_dry_run"

WEEKDAY_DE = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
WEEKDAY_EN = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _blok_login(page, base_url: str, login_path: str, username: str, password: str, selectors: dict) -> None:
    page.goto(base_url + login_path, wait_until="networkidle", timeout=60000)

    sel_user = selectors.get("username", 'input[name="uid:border:classAdder:field"]')
    sel_pass = selectors.get("password", 'input[type="password"]')
    sel_btn = selectors.get("login_button", 'button:has-text("Anmelden")')

    if not page.locator(sel_user).count() or not page.locator(sel_pass).count():
        raise RuntimeError("Form login BLok tidak ditemukan. Cek login_path di config.yaml.")

    page.fill(sel_user, username)
    page.fill(sel_pass, password)
    with page.expect_response(lambda r: "submitLogin" in r.url, timeout=30000):
        page.locator(sel_btn).first.click()
    page.wait_for_url("**/blok/home**", timeout=30000)

    body = page.inner_text("body")
    if "Falsches Passwort" in body:
        raise RuntimeError(
            "Login BLok gagal: password salah. Perbarui Keychain: "
            "python3 -m berichtsheft credentials set --service blok"
        )


def _blok_hours_value(conn, iso_date: str, payload: dict[str, Any]) -> str:
    """Jam di form BLok: default 8h dari aturan, atau dari draft."""
    return stunden_for_blok(conn, iso_date) or payload.get("hours") or DEFAULT_STUNDEN


def _weekday_index(iso_date: str) -> int:
    return date.fromisoformat(iso_date).weekday()  # 0=Mo


def _blok_save_day(page, day_idx: int) -> bool:
    """
    Simpan hari tertentu di form Woche.
    Tombol 'Nochmal speichern!' tersembunyi (display:none) — pakai JS BLok asli.
    """
    save_link = page.locator("a.savebutton").nth(day_idx)
    if not save_link.count():
        return False
    onclick = save_link.get_attribute("onclick") or ""
    match = re.search(r"blokUpdateSaveStateSave\('([^']+)'\)", onclick)
    if not match:
        return False
    save_id = match.group(1)
    page.evaluate("(id) => blokUpdateSaveStateSave(id)", save_id)
    page.wait_for_load_state("networkidle", timeout=30000)
    return True


def _draft_payload(conn, iso_date: str) -> dict[str, Any]:
    row = db.get_draft(conn, iso_date)
    if not row:
        raise ValueError(f"No draft for {iso_date}. Run finish first.")
    return {
        "date": row["date"],
        "hours": row["hours"],
        "ort": row["ort"],
        "lernfeld": row["lernfeld"],
        "taetigkeiten": row["taetigkeiten"],
        "status": row["status"],
    }


def dry_run_fill(conn, iso_date: str) -> Path:
    payload = _draft_payload(conn, iso_date)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>BLok Dry Run {iso_date}</title></head>
<body>
<h1>BLok Dry Run — {iso_date}</h1>
<p><b>Ort:</b> {payload['ort']}</p>
<p><b>Stunden:</b> {payload.get('hours') or '—'}</p>
<p><b>Lernfeld:</b> {payload.get('lernfeld') or '—'}</p>
<h2>Tätigkeiten</h2>
<pre>{payload['taetigkeiten']}</pre>
</body></html>"""
    out = OUTPUT_DIR / f"{iso_date}.html"
    out.write_text(html, encoding="utf-8")
    json_path = OUTPUT_DIR / f"{iso_date}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    db.update_draft_status(conn, iso_date, "filled_dry_run")
    return out


def live_fill(conn, iso_date: str) -> dict[str, Any]:
    cred = credentials.get_credential("blok")
    if not cred:
        raise RuntimeError(
            "BLok credentials missing. Run: python3 -m berichtsheft credentials set --service blok"
        )
    username, password = cred
    payload = _draft_payload(conn, iso_date)
    cfg = load_config()
    blok = cfg.get("blok") or {}
    base_url = blok.get("base_url", "https://www.online-ausbildungsnachweis.de")
    selectors = blok.get("selectors") or {}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError("Install playwright: pip install playwright && playwright install chromium") from e

    if " " in username or "python" in username.lower():
        raise RuntimeError(
            f"Username Keychain tidak valid: '{username[:40]}...'. "
            "Jalankan: python3 -m berichtsheft credentials set --service blok"
        )

    status_msg = ""
    saved = False
    day_de = WEEKDAY_DE[_weekday_index(iso_date)]
    fields_applied = None
    screenshot = OUTPUT_DIR / f"{iso_date}_live.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        login_path = blok.get("login_path", "/blok/login")
        _blok_login(page, base_url, login_path, username, password, selectors)

        report_path = blok.get("report_path", "/blok/report")
        page.goto(base_url + report_path, wait_until="networkidle", timeout=60000)

        target = date.fromisoformat(iso_date)
        if not go_to_week_containing_with_fallback(page, target):
            browser.close()
            raise RuntimeError(
                f"Tidak bisa navigasi ke minggu untuk {iso_date}. Buka BLok manual lalu coba lagi."
            )

        allowed, status_msg = live_fill_allowed(page)
        if not allowed:
            browser.close()
            raise RuntimeError(status_msg)

        shift = db.get_shift(conn, iso_date)
        fmt = (blok.get("format") or "tag").lower()
        day_idx = _weekday_index(iso_date)
        day_en = WEEKDAY_EN[day_idx]
        day_de = WEEKDAY_DE[day_idx]

        fields_applied = None
        if shift and fmt == "woche":
            shift_d = dict(shift)
            try:
                shift_d["tags"] = json.loads(shift["tags_json"] or "[]")
            except (json.JSONDecodeError, TypeError):
                shift_d["tags"] = []
            fields_applied = apply_day_fields(page, day_en, day_idx, shift_d)

        if fmt == "woche":
            sel_ta = f'textarea[name="tableComp:{day_en}:inputs:0:report"]'
            ta = page.locator(sel_ta)
            if not ta.count():
                if day_idx >= 5:
                    browser.close()
                    raise RuntimeError(
                        f"{day_de} ({iso_date}): BLok menampilkan 'Wochenende' tanpa field isian. "
                        "Isi manual di BLok atau buka minggu yang benar."
                    )
                raise RuntimeError(
                    f"Textarea {day_de} tidak ditemukan. Buka KW yang benar di BLok lalu coba lagi."
                )
            ta.first.fill(payload["taetigkeiten"])
            ta.first.dispatch_event("change")
            blok_hours = _blok_hours_value(conn, iso_date, payload)
            sel_h = f'input[name="tableComp:{day_en}:inputs:0:has"]'
            if blok_hours and page.locator(sel_h).count():
                hours_el = page.locator(sel_h).first
                hours_el.click()
                hours_el.fill(blok_hours)
                hours_el.dispatch_event("input")
                hours_el.dispatch_event("change")
                hours_el.dispatch_event("blur")
        else:
            sel_text = selectors.get("activity_text", "textarea")
            if page.locator(sel_text).count():
                page.fill(sel_text, payload["taetigkeiten"])
            sel_hours = selectors.get("hours_field")
            if sel_hours and payload.get("hours") and page.locator(sel_hours).count():
                page.fill(sel_hours, payload["hours"])

        auto_save = blok.get("auto_save", True)
        saved = _blok_save_day(page, day_idx) if auto_save else False

        screenshot = OUTPUT_DIR / f"{iso_date}_live.png"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(screenshot), full_page=True)

        browser.close()

    status = "saved_live" if saved else "filled_live"
    db.update_draft_status(conn, iso_date, status)
    note = "Tersimpan di BLok." if saved else "Terisi tapi belum disimpan."
    if status_msg:
        note = f"{status_msg} {note}"
    return {
        "date": iso_date,
        "saved": saved,
        "day": day_de,
        "fields": fields_applied,
        "screenshot": str(screenshot),
        "note": note,
    }


def _shift_policy(conn, iso_date: str) -> dict[str, Any]:
    """Kebijakan isi BLok mengikuti EdTime, bukan hari kalender."""
    shift = db.get_shift(conn, iso_date)
    if not shift:
        return {"fill": False, "reason": "no_shift", "day_type": None}
    day_type = shift["day_type"]
    if day_type == "frei":
        return {"fill": False, "reason": "ausgang_edtime", "day_type": day_type}
    return {"fill": True, "reason": "ok", "day_type": day_type}


def run_worker(conn, iso_date: str, *, dry_run: bool = True, live: bool = False) -> dict[str, Any]:
    policy = _shift_policy(conn, iso_date)
    if not policy["fill"]:
        return {
            "date": iso_date,
            "skipped": True,
            "reason": policy["reason"],
            "day_type": policy["day_type"],
            "hint": "Hari libur (Ausgang) di EdTime — tidak diisi BLok.",
        }

    draft = db.get_draft(conn, iso_date)
    if draft and draft["status"] == "skipped":
        return {"date": iso_date, "skipped": True, "reason": "draft_skipped"}

    if live and not dry_run:
        return live_fill(conn, iso_date)
    path = dry_run_fill(conn, iso_date)
    return {"date": iso_date, "dry_run": True, "output": str(path)}
