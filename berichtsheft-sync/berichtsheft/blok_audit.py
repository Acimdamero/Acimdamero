"""Audit penuh laporan BLok lama — navigasi klik, bukan page.goto href."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from berichtsheft import credentials
from berichtsheft.blok_nav import _click_week, week_range
from berichtsheft.blok_status import detect_week_status
from berichtsheft.blok_worker import _blok_login
from berichtsheft.config_loader import ROOT, load_config

OUTPUT_DIR = ROOT / "output" / "blok_audit"

WEEKDAY_EN = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)
WEEKDAY_DE = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
DAY_HEADER_RE = re.compile(
    r"(Mo|Di|Mi|Do|Fr|Sa|So)\s+(\d{2}\.\d{2}\.)",
    re.MULTILINE,
)


def _select_value(page, name: str) -> str | None:
    loc = page.locator(f'select[name="{name}"]')
    if not loc.count():
        return None
    try:
        opt = loc.first.locator("option:checked")
        if opt.count():
            return opt.first.inner_text().strip()
        return loc.first.input_value()
    except Exception:
        return None


def _read_editable_day(page, day_en: str) -> dict[str, Any]:
    ta_sel = f'textarea[name="tableComp:{day_en}:inputs:0:report"]'
    has_sel = f'input[name="tableComp:{day_en}:inputs:0:has"]'
    ta = page.locator(ta_sel)
    has_inp = page.locator(has_sel)
    text = ta.input_value().strip() if ta.count() else ""
    hours = has_inp.input_value().strip() if has_inp.count() else ""
    return {
        "mode": "editable",
        "has_field": ta.count() > 0,
        "text": text or None,
        "text_len": len(text),
        "hours": hours or None,
        "presence": _select_value(page, f"tableComp:{day_en}:trspaceplus:presence"),
        "location": _select_value(page, f"tableComp:{day_en}:trspaceplus:location"),
    }


def _parse_readonly_days(body: str) -> dict[str, str]:
    """Ekstrak blok teks per hari dari body read-only (minggu abgenommen)."""
    chunks: dict[str, str] = {}
    matches = list(DAY_HEADER_RE.finditer(body))
    for i, m in enumerate(matches):
        day = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        chunk = body[start:end].strip()
        chunk = re.sub(r"\n{3,}", "\n\n", chunk)
        chunks[day] = chunk
    return chunks


def _read_readonly_day(body: str, day_de: str) -> dict[str, Any]:
    chunks = _parse_readonly_days(body)
    text = chunks.get(day_de, "").strip()
    hours_m = re.search(r"(\d+h:\d{2}min)", text)
    presence_m = re.search(
        r"(Anwesend|Abwesend|Urlaub|Wochenende|Feiertag|Sonderurlaub|Arbeitsunfähig)",
        text,
    )
    location_m = re.search(
        r"(Berufsschule|Ausbildungsbetrieb|Überbetrieblich)",
        text,
    )
    return {
        "mode": "readonly",
        "has_field": False,
        "text": text[:4000] if text else None,
        "text_len": len(text),
        "hours": hours_m.group(1) if hours_m else None,
        "presence": presence_m.group(1) if presence_m else None,
        "location": location_m.group(1) if location_m else None,
    }


def _audit_current_week(page) -> dict[str, Any]:
    ws, we = week_range(page)
    status_info = detect_week_status(page)
    body = page.inner_text("body")
    editable = status_info["editable"]

    days: list[dict[str, Any]] = []
    for i, (en, de) in enumerate(zip(WEEKDAY_EN, WEEKDAY_DE)):
        iso = (ws + timedelta(days=i)).isoformat() if ws else None
        if editable:
            day_data = _read_editable_day(page, en)
        else:
            day_data = _read_readonly_day(body, de)
        day_data["day"] = de
        day_data["iso_date"] = iso
        days.append(day_data)

    filled = sum(1 for d in days if (d.get("text_len") or 0) > 0 or d.get("hours"))
    return {
        "week_start": str(ws) if ws else None,
        "week_end": str(we) if we else None,
        "status": status_info["status"],
        "editable": editable,
        "days_filled": filled,
        "days": days,
    }


def _navigate_to_first_week(page, start: date, *, max_steps: int = 70) -> bool:
    for _ in range(max_steps):
        ws, we = week_range(page)
        if ws and ws <= start:
            return True
        if not ws:
            return False
        if not _click_week(page, "back"):
            break
    ws, _ = week_range(page)
    return bool(ws and ws <= start)


def audit_range(
    from_date: date,
    to_date: date,
    *,
    headless: bool = True,
) -> dict[str, Any]:
    cred = credentials.get_credential("blok")
    if not cred:
        raise RuntimeError(
            "BLok credentials missing. Run: python3 -m berichtsheft credentials set --service blok"
        )
    username, password = cred
    cfg = load_config()
    blok = cfg.get("blok") or {}
    base_url = blok.get("base_url", "https://www.online-ausbildungsnachweis.de")
    selectors = blok.get("selectors") or {}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "Install playwright: pip install playwright && playwright install chromium"
        ) from e

    report: dict[str, Any] = {
        "generated": datetime.now().isoformat(),
        "range": {"from": str(from_date), "to": str(to_date)},
        "weeks": [],
        "summary": {},
        "errors": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        login_path = blok.get("login_path", "/blok/login")
        _blok_login(page, base_url, login_path, username, password, selectors)

        report_path = blok.get("report_path", "/blok/report")
        page.goto(base_url + report_path, wait_until="networkidle", timeout=60000)

        if not _navigate_to_first_week(page, from_date):
            report["errors"].append(f"Tidak bisa navigasi ke minggu >= {from_date}")

        seen: set[str] = set()
        for _ in range(60):
            ws, we = week_range(page)
            if not ws or not we:
                report["errors"].append("Kalenderwoche tidak terbaca")
                break
            key = str(ws)
            if key in seen:
                report["errors"].append(f"Loop navigasi di {key}")
                break
            seen.add(key)

            if we >= from_date and ws <= to_date:
                report["weeks"].append(_audit_current_week(page))

            if ws > to_date:
                break
            if not _click_week(page, "forward"):
                break

        browser.close()

    weeks = report["weeks"]
    report["summary"] = {
        "weeks_scanned": len(weeks),
        "editable_weeks": sum(1 for w in weeks if w.get("editable")),
        "abgenommen_weeks": sum(1 for w in weeks if w.get("status") == "abgenommen"),
        "days_with_content": sum(w.get("days_filled", 0) for w in weeks),
    }
    return report


def run_audit(
    from_iso: str,
    to_iso: str,
    *,
    headless: bool = True,
) -> Path:
    from_date = date.fromisoformat(from_iso)
    to_date = date.fromisoformat(to_iso)
    report = audit_range(from_date, to_date, headless=headless)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def print_audit_summary(report: dict[str, Any], gap_weeks: list | None = None) -> None:
    s = report.get("summary") or {}
    print(f"Minggu di-scan: {s.get('weeks_scanned', 0)}")
    print(f"Bearbeitbar: {s.get('editable_weeks', 0)}")
    print(f"Abgenommen: {s.get('abgenommen_weeks', 0)}")
    print(f"Hari berisi teks/jam: {s.get('days_with_content', 0)}")
    if gap_weeks:
        total = sum(g.get("summary", {}).get("issue_count", 0) for g in gap_weeks)
        print(f"Isu gap (EdTime vs BLok): {total}")
        for g in gap_weeks:
            issues = [
                i for i in g.get("issues", [])
                if i.get("severity") in ("high", "medium")
            ]
            if issues:
                print(f"  KW {g.get('week_start')}:")
                for i in issues[:5]:
                    print(f"    - {i['message']}")
    if report.get("errors"):
        print("Peringatan:")
        for err in report["errors"]:
            print(f"  - {err}")
