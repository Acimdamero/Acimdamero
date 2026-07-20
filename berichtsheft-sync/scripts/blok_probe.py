#!/usr/bin/env python3
"""Probe BLok login + report page structure (read-only diagnostic)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from berichtsheft import credentials
from berichtsheft.config_loader import load_config


def main() -> int:
    cred = credentials.get_credential("blok")
    if not cred:
        print("NO_CREDENTIALS")
        return 1
    username, password = cred
    cfg = load_config()
    blok = cfg.get("blok") or {}
    base_url = blok.get("base_url", "https://www.online-ausbildungsnachweis.de")
    selectors = blok.get("selectors") or {}

    from playwright.sync_api import sync_playwright

    out = {"steps": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        login_urls = [
            base_url + blok.get("login_path", "/blok/login"),
            base_url + "/blok/login",
            base_url + "/",
        ]
        login_ok = False
        for url in login_urls:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            out["steps"].append({"goto": url, "title": page.title(), "final_url": page.url})

            sel_user = selectors.get("username", 'input[type="text"]')
            sel_pass = selectors.get("password", 'input[type="password"]')
            sel_btn = selectors.get("login_button", 'button[type="submit"]')

            user_count = page.locator(sel_user).count()
            pass_count = page.locator(sel_pass).count()
            btn_count = page.locator(sel_btn).count()
            out["login_form"] = {"url": page.url, "user": user_count, "pass": pass_count, "btn": btn_count}

            if user_count and pass_count:
                page.fill(sel_user, username)
                page.fill(sel_pass, password)
                if btn_count:
                    page.click(sel_btn)
                    page.wait_for_load_state("networkidle", timeout=60000)
                out["steps"].append({"after_login": page.url, "title": page.title()})
                login_ok = True
                break
        out["login_ok"] = login_ok

        # Try common report paths
        candidates = [
            blok.get("report_path", "/blok/report"),
            "/blok",
            "/berichtsheft",
            "/app",
            "/dashboard",
        ]
        for path in candidates:
            if not path:
                continue
            try:
                page.goto(base_url + path, wait_until="domcontentloaded", timeout=30000)
                ta = page.locator("textarea").count()
                inp = page.locator('input[type="text"]').count()
                out["steps"].append({
                    "path": path,
                    "url": page.url,
                    "title": page.title(),
                    "textareas": ta,
                    "text_inputs": inp,
                })
            except Exception as e:
                out["steps"].append({"path": path, "error": str(e)})

        shot = ROOT / "output" / "blok_dry_run" / "probe.png"
        shot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(shot), full_page=True)
        out["screenshot"] = str(shot)

        # Links on current page containing woche/report/bericht
        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({href: e.href, text: (e.innerText||'').trim().slice(0,80)}))",
        )
        keywords = ("woche", "bericht", "report", "nachweis", "blok")
        out["interesting_links"] = [
            l for l in links if any(k in (l.get("href") or "").lower() or k in (l.get("text") or "").lower() for k in keywords)
        ][:30]

        browser.close()

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
