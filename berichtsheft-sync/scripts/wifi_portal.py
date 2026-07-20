#!/usr/bin/env python3
"""Company WiFi captive portal — click login without password."""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from berichtsheft.config_loader import load_config  # noqa: E402


def current_ssid() -> str | None:
    if platform.system() != "Darwin":
        return None
    try:
        out = subprocess.check_output(
            [
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                "-I",
            ],
            text=True,
        )
        for line in out.splitlines():
            if " SSID:" in line:
                return line.split(":", 1)[1].strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    try:
        out = subprocess.check_output(
            ["networksetup", "-getairportnetwork", "en0"],
            text=True,
        )
        if ":" in out:
            return out.split(":", 1)[1].strip()
    except subprocess.CalledProcessError:
        pass
    return None


def internet_ok() -> bool:
    try:
        subprocess.check_call(
            ["ping", "-c", "1", "-W", "2", "1.1.1.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def run_portal_login(dry_run: bool = False) -> int:
    cfg = load_config().get("wifi") or {}
    expected_ssid = cfg.get("ssid", "")
    portal_url = cfg.get("portal_url", "")
    selector = cfg.get("login_button_selector", "button")

    ssid = current_ssid()
    print(f"SSID saat ini: {ssid!r}")

    if expected_ssid and ssid != expected_ssid:
        print(f"Lewati — bukan SSID target ({expected_ssid})")
        return 0

    if internet_ok():
        print("Internet OK — portal tidak diperlukan")
        return 0

    if not portal_url:
        print("wifi.portal_url belum diisi di config.yaml")
        return 1

    if dry_run:
        print(f"[dry-run] Buka {portal_url} → klik {selector}")
        return 0

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("pip install playwright && playwright install chromium")
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(portal_url, timeout=60000)
        loc = page.locator(selector).first
        if loc.count():
            loc.click()
            print("Tombol login diklik.")
        else:
            print(f"Selector tidak ditemukan: {selector}")
        page.wait_for_timeout(3000)
        browser.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return run_portal_login(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
