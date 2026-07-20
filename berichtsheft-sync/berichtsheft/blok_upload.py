"""Upload lampiran ke BLok Dokumentenablage + einbinden di Berichtsheft."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from berichtsheft import credentials, db
from berichtsheft.blok_nav import go_to_week_containing
from berichtsheft.blok_worker import _blok_login, WEEKDAY_EN
from berichtsheft.config_loader import ROOT, load_config

WEEKDAY_INDEX = {en: i for i, en in enumerate(WEEKDAY_EN)}


def _navigate_dokumentenablage(page, base_url: str) -> None:
    page.locator('a:has-text("Entwicklungsportfolio")').first.click(force=True)
    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(800)
    page.locator('a:has-text("Dokumentenablage")').first.click(force=True)
    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(1200)


def _portfolio_has_file(page, filename: str) -> bool:
    return filename in page.inner_text("body")


def upload_to_portfolio(page, file_path: Path) -> str:
    """Upload file ke Dokumentenablage. Return nama file di BLok."""
    if not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    filename = file_path.name
    if _portfolio_has_file(page, filename):
        return filename

    page.locator('button:has-text("Datei hochladen")').first.click(force=True)
    page.wait_for_timeout(800)
    page.locator('input[type="file"]').set_input_files(str(file_path.resolve()))
    page.wait_for_timeout(500)
    page.locator('button:has-text("Hochladen")').last.click(force=True)
    page.wait_for_load_state("networkidle", timeout=90000)
    page.wait_for_timeout(2000)

    if not _portfolio_has_file(page, filename):
        raise RuntimeError(f"Upload gagal — {filename} tidak muncul di Dokumentenablage")
    return filename


def _select_file_in_attach_dialog(page, filename: str) -> bool:
    checkboxes = page.locator(
        'input[type="checkbox"][name*="listCon"][name*="firstCol:select"]'
    )
    for i in range(checkboxes.count()):
        row = checkboxes.nth(i).locator("xpath=ancestor::tr[1]")
        if row.count() and filename in row.inner_text():
            checkboxes.nth(i).check(force=True)
            return True
    return False


def bind_file_to_day(page, base_url: str, iso_date: str, filename: str) -> bool:
    """Pilih file dari Dokumentenablage → Im Berichtsheft einbinden untuk hari iso_date."""
    target = date.fromisoformat(iso_date)
    page.goto(base_url + "/blok/report", wait_until="networkidle", timeout=60000)
    if not go_to_week_containing(page, target):
        raise RuntimeError(f"Tidak bisa navigasi ke minggu {iso_date}")

    day_en = WEEKDAY_EN[target.weekday()]
    day_idx = WEEKDAY_INDEX[day_en]
    attach_links = page.locator('a:has-text("Datei anhängen")')
    if attach_links.count() <= day_idx:
        raise RuntimeError(f"Link Datei anhängen tidak ada untuk {iso_date}")
    attach_links.nth(day_idx).click(force=True)
    page.wait_for_timeout(1500)

    if not _select_file_in_attach_dialog(page, filename):
        raise RuntimeError(f"File {filename} tidak ditemukan di dialog lampiran")

    bind_btn = page.locator('button:has-text("Im Berichtsheft einbinden")')
    if not bind_btn.count():
        raise RuntimeError("Tombol 'Im Berichtsheft einbinden' tidak ditemukan")
    bind_btn.first.click(force=True)
    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(1500)
    return True


def upload_attachment(
    conn,
    attachment_id: int,
    *,
    bind: bool = True,
    headless: bool = True,
) -> dict[str, Any]:
    row = db.get_attachment(conn, attachment_id)
    if not row:
        raise ValueError(f"Lampiran #{attachment_id} tidak ada")

    fpath = ROOT / row["path"]
    if not fpath.is_file():
        raise FileNotFoundError(f"File hilang: {row['path']}")

    iso_date = row["date"]
    cred = credentials.get_credential("blok")
    if not cred:
        raise RuntimeError("BLok credentials missing")

    cfg = load_config()
    blok = cfg.get("blok") or {}
    base_url = blok.get("base_url", "https://www.online-ausbildungsnachweis.de")
    selectors = blok.get("selectors") or {}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError("Install playwright") from e

    username, password = cred
    now = datetime.now().isoformat(timespec="seconds")
    result: dict[str, Any] = {
        "attachment_id": attachment_id,
        "date": iso_date,
        "path": row["path"],
        "bound": False,
    }

    filename = row["blok_filename"] if row["blok_status"] in ("uploaded", "bound") else None

    with sync_playwright() as p:
        page = p.chromium.launch(headless=headless).new_page()
        login_path = blok.get("login_path", "/blok/login")
        _blok_login(page, base_url, login_path, username, password, selectors)

        if not filename:
            _navigate_dokumentenablage(page, base_url)
            filename = upload_to_portfolio(page, fpath)
            result["blok_filename"] = filename
            db.update_attachment_blok(
                conn, attachment_id, "uploaded", blok_filename=filename, uploaded_at=now
            )
        else:
            result["blok_filename"] = filename

        if bind and row["blok_status"] != "bound":
            bind_file_to_day(page, base_url, iso_date, filename)
            result["bound"] = True
            db.update_attachment_blok(
                conn, attachment_id, "bound", bound_at=datetime.now().isoformat(timespec="seconds")
            )
        elif row["blok_status"] == "bound":
            result["bound"] = True

        page.context.browser.close()

    return result


def upload_attachments_for_date(
    conn,
    iso_date: str,
    attachment_ids: list[int] | None = None,
    *,
    bind: bool = True,
    headless: bool = True,
) -> list[dict[str, Any]]:
    if attachment_ids:
        rows = [db.get_attachment(conn, aid) for aid in attachment_ids]
        rows = [r for r in rows if r and r["date"] == iso_date]
    else:
        rows = db.attachments_for_date(conn, iso_date)

    results = []
    for row in rows:
        if row["blok_status"] == "bound":
            results.append(
                {
                    "attachment_id": row["id"],
                    "date": iso_date,
                    "skipped": True,
                    "reason": "already_bound",
                    "blok_filename": row["blok_filename"],
                }
            )
            continue
        try:
            results.append(
                upload_attachment(conn, row["id"], bind=bind, headless=headless)
            )
        except Exception as e:
            db.update_attachment_blok(conn, row["id"], "failed")
            results.append(
                {"attachment_id": row["id"], "date": iso_date, "error": str(e)}
            )
    return results
