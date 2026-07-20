#!/usr/bin/env python3
"""Eksplorasi BLok: navigasi + scan minggu Agustus 2025 – sekarang."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from berichtsheft import credentials

BASE = "https://www.online-ausbildungsnachweis.de"
OUT = ROOT / "output" / "blok_explore"
START = date(2025, 8, 1)
END = date(2026, 6, 5)


def login(page, user: str, pwd: str) -> None:
    page.goto(BASE + "/blok/login", wait_until="networkidle", timeout=60000)
    page.fill('input[name="uid:border:classAdder:field"]', user)
    page.fill('input[type="password"]', pwd)
    with page.expect_response(lambda r: "submitLogin" in r.url, timeout=30000):
        page.locator('button:has-text("Anmelden")').first.click()
    page.wait_for_url("**/blok/home**", timeout=30000)


def nav_links(page) -> list[dict]:
    return page.eval_on_selector_all(
        "a[href]",
        """els => els.map(e => ({
            text: (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 80),
            href: e.href
        })).filter(x => x.text)""",
    )


def main() -> int:
    cred = credentials.get_credential("blok")
    if not cred:
        print("NO_CREDENTIALS")
        return 1
    user, pwd = cred

    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    report: dict = {
        "generated": datetime.now().isoformat(),
        "range": {"from": str(START), "to": str(END)},
        "navigation": {},
        "interface": {},
        "weeks": [],
        "errors": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        login(page, user, pwd)

        # --- Navigasi utama ---
        page.goto(BASE + "/blok/home", wait_until="networkidle", timeout=60000)
        main_nav = [
            l for l in nav_links(page)
            if any(k in l["text"].lower() for k in ("übersicht", "berichtsheft", "ausbilder", "nachrichten", "portfolio", "einstellungen"))
        ]
        report["navigation"]["home_main"] = main_nav[:20]

        # Kunjungi setiap tab utama
        tabs = {
            "Übersicht": None,
            "Berichtsheft": BASE + "/blok/report",
            "Ausbilder": None,
            "Nachrichten": None,
            "Entwicklungsportfolio": None,
            "Einstellungen": None,
        }
        for label in tabs:
            link = page.locator(f"a:has-text('{label}')").first
            if link.count():
                href = link.get_attribute("href")
                tabs[label] = href
        report["navigation"]["tabs_href"] = tabs

        # Berichtsheft sub-nav
        page.goto(BASE + "/blok/report", wait_until="networkidle", timeout=60000)
        sub = page.eval_on_selector_all(
            "a, button",
            """els => els.map(e => (e.innerText || e.value || '').trim())
                .filter(t => /^(Export|Heute|Woche|Jahresansicht|Ausbildungsverlauf|Bearbeitungsmodus)$/i.test(t)
                    || /Woche (zurück|vor)/i.test(t)
                    || /freigeben/i.test(t))""",
        )
        report["interface"]["berichtsheft_subnav"] = sub

        # Dropdown status & abteilung
        selects = page.eval_on_selector_all(
            "select",
            """els => els.map(e => ({
                name: e.name || '',
                id: e.id || '',
                options: [...e.options].slice(0, 30).map(o => o.text.trim())
            }))""",
        )
        report["interface"]["selects_on_report"] = selects

        # Scan minggu: navigasi ke minggu yang mengandung START
        def week_label() -> str:
            body = page.inner_text("body")
            m = re.search(r"(\d+)\.\s*Kalenderwoche vom (\d{2}\.\d{2}\.\d{4}) bis (\d{2}\.\d{2}\.\d{4})", body)
            return m.group(0) if m else ""

        def week_dates() -> tuple[date | None, date | None]:
            body = page.inner_text("body")
            m = re.search(r"Kalenderwoche vom (\d{2})\.(\d{2})\.(\d{4}) bis (\d{2})\.(\d{2})\.(\d{4})", body)
            if not m:
                return None, None
            d1, m1, y1, d2, m2, y2 = map(int, m.groups())
            return date(y1, m1, d1), date(y2, m2, d2)

        def day_summary() -> list[dict]:
            days_en = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
            days_de = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
            rows = []
            for i, (en, de) in enumerate(zip(days_en, days_de)):
                ta_sel = f'textarea[name="tableComp:{en}:inputs:0:report"]'
                has_sel = f'input[name="tableComp:{en}:inputs:0:has"]'
                ta = page.locator(ta_sel)
                has_inp = page.locator(has_sel)
                text = ta.input_value().strip() if ta.count() else ""
                hours = has_inp.input_value().strip() if has_inp.count() else ""
                # status dropdowns near day row — approximate via name patterns
                rows.append({
                    "day": de,
                    "has_field": ta.count() > 0,
                    "hours": hours or None,
                    "text_len": len(text),
                    "text_preview": text[:120] if text else None,
                })
            return rows

        # Ke belakang sampai sebelum START
        back_btn = page.locator("a:has-text('Eine Woche zurück'), button:has-text('Eine Woche zurück')")
        forward_btn = page.locator("a:has-text('Eine Woche vor'), button:has-text('Eine Woche vor')")

        if not back_btn.count():
            report["errors"].append("Tombol 'Eine Woche zurück' tidak ditemukan")

        # Fast-forward ke belakang dulu (max 60 klik) sampai week_start <= START atau stuck
        for _ in range(60):
            ws, we = week_dates()
            if ws and ws <= START:
                break
            if not back_btn.count():
                break
            back_btn.first.click()
            page.wait_for_load_state("networkidle", timeout=30000)
        else:
            report["errors"].append("Tidak bisa navigasi ke Agustus 2025 dalam 60 klik")

        # Scan minggu demi minggu ke depan
        seen = set()
        max_weeks = 55  # ~Aug 2025 – Jun 2026
        for _ in range(max_weeks):
            label = week_label()
            ws, we = week_dates()
            if not ws or not we:
                report["errors"].append(f"Minggu tidak terbaca: {label}")
                break
            key = str(ws)
            if key in seen:
                report["errors"].append(f"Loop navigasi di {key}")
                break
            seen.add(key)

            days = day_summary()
            filled = sum(1 for d in days if d["text_len"] > 0 or (d["hours"] and d["hours"] != "0h:00min"))
            report["weeks"].append({
                "kw_label": label,
                "week_start": str(ws),
                "week_end": str(we),
                "days_filled": filled,
                "days": days,
            })

            if we >= END:
                break
            if not forward_btn.count():
                break
            forward_btn.first.click()
            page.wait_for_load_state("networkidle", timeout=30000)

        # Jahresansicht
        page.goto(BASE + "/blok/report", wait_until="networkidle", timeout=30000)
        ja = page.locator("a:has-text('Jahresansicht')")
        if ja.count():
            ja.first.click()
            page.wait_for_load_state("networkidle", timeout=30000)
            report["interface"]["jahresansicht_url"] = page.url
            report["interface"]["jahresansicht_snippet"] = page.inner_text("body")[:1500]

        page.screenshot(path=str(OUT / "explore_last.png"), full_page=True)
        browser.close()

    out_path = OUT / "scan_aug2025_now.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "weeks_scanned": len(report["weeks"]),
        "first_week": report["weeks"][0] if report["weeks"] else None,
        "last_week": report["weeks"][-1] if report["weeks"] else None,
        "errors": report["errors"],
        "output": str(out_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
