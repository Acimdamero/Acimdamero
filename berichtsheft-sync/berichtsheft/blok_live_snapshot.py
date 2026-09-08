"""BLok live login snapshot for dashboard (Playwright).

Saves post-login (or failed-login) screenshot under output/blok_live/.
Credentials: Keychain / secrets file / BLOK_USERNAME+BLOK_PASSWORD env.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from berichtsheft import credentials
from berichtsheft.config_loader import ROOT, load_config, load_dotenv

LIVE_DIR = ROOT / "output" / "blok_live"
LATEST_PNG = LIVE_DIR / "latest.png"
LATEST_META = LIVE_DIR / "meta.json"

DEFAULT_BASE_URL = "https://www.online-ausbildungsnachweis.de"
DEFAULT_LOGIN_PATH = "/blok/login"

# Prefer config selectors, then known BLok / Wicket variants.
_USER_SELECTORS = (
    'input[name="uid:border:classAdder:field"]',
    'input[name="username"]',
    'input[type="text"]',
    'input[name="uid"]',
    "#username",
)
_PASS_SELECTORS = (
    'input[type="password"]',
    'input[name="password"]',
)
_BTN_SELECTORS = (
    'button:has-text("Anmelden")',
    'input[type="submit"]',
    'button[type="submit"]',
    'button:has-text("Login")',
)


def resolve_base_url(cfg: dict[str, Any] | None = None) -> str:
    """BLOK_BASE_URL env overrides config.yaml blok.base_url."""
    load_dotenv()
    env = (os.environ.get("BLOK_BASE_URL") or "").strip().rstrip("/")
    if env:
        return env
    blok = (cfg or load_config()).get("blok") or {}
    return str(blok.get("base_url") or DEFAULT_BASE_URL).rstrip("/")


def resolve_login_path(cfg: dict[str, Any] | None = None) -> str:
    blok = (cfg or load_config()).get("blok") or {}
    path = str(blok.get("login_path") or DEFAULT_LOGIN_PATH)
    if not path.startswith("/"):
        path = "/" + path
    return path


def _first_visible(page, candidates: tuple[str, ...] | list[str]) -> str | None:
    for sel in candidates:
        loc = page.locator(sel)
        try:
            if loc.count() and loc.first.is_visible():
                return sel
        except Exception:  # noqa: BLE001 — probe next selector
            continue
    return None


def _login_selectors(cfg: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    blok = cfg.get("blok") or {}
    selectors = blok.get("selectors") or {}
    user = [selectors["username"]] if selectors.get("username") else []
    pwd = [selectors["password"]] if selectors.get("password") else []
    btn = [selectors["login_button"]] if selectors.get("login_button") else []
    return (
        user + [s for s in _USER_SELECTORS if s not in user],
        pwd + [s for s in _PASS_SELECTORS if s not in pwd],
        btn + [s for s in _BTN_SELECTORS if s not in btn],
    )


def _write_meta(meta: dict[str, Any]) -> Path:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_META.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return LATEST_META


def read_latest_meta() -> dict[str, Any] | None:
    if not LATEST_META.is_file():
        return None
    try:
        return json.loads(LATEST_META.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def take_live_snapshot(*, timeout_ms: int = 60000) -> dict[str, Any]:
    """Login to BLok and save screenshot + meta. Never returns passwords."""
    load_dotenv()
    cfg = load_config()
    base_url = resolve_base_url(cfg)
    login_path = resolve_login_path(cfg)
    login_url = base_url + login_path

    now = datetime.now(timezone.utc).isoformat()
    cred = credentials.get_credential("blok")
    if not cred:
        meta = {
            "ok": False,
            "logged_in": False,
            "status": "no_credentials",
            "error": (
                "BLok credentials missing. Set BLOK_USERNAME + BLOK_PASSWORD "
                "in .env (cloud) or Keychain on Mac."
            ),
            "login_url": login_url,
            "base_url": base_url,
            "taken_at": now,
            "image_path": None,
            "image_url": None,
        }
        _write_meta(meta)
        return meta

    username, password = cred
    if " " in username or "python" in username.lower():
        meta = {
            "ok": False,
            "logged_in": False,
            "status": "invalid_username",
            "error": "Stored username looks invalid (not a BLok login id).",
            "login_url": login_url,
            "base_url": base_url,
            "taken_at": now,
            "username_hint": username[:3] + "…" if len(username) > 3 else "***",
            "image_path": None,
            "image_url": None,
        }
        _write_meta(meta)
        return meta

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        meta = {
            "ok": False,
            "logged_in": False,
            "status": "playwright_missing",
            "error": (
                "Install playwright: pip install playwright && "
                "python3 -m playwright install chromium"
            ),
            "login_url": login_url,
            "base_url": base_url,
            "taken_at": now,
            "image_path": None,
            "image_url": None,
        }
        _write_meta(meta)
        raise RuntimeError(meta["error"]) from e

    user_sels, pass_sels, btn_sels = _login_selectors(cfg)
    LIVE_DIR.mkdir(parents=True, exist_ok=True)

    logged_in = False
    status = "failed"
    error: str | None = None
    final_url = login_url
    title = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto(login_url, wait_until="domcontentloaded", timeout=timeout_ms)
            sel_user = _first_visible(page, user_sels)
            sel_pass = _first_visible(page, pass_sels)
            sel_btn = _first_visible(page, btn_sels)
            if not sel_user or not sel_pass:
                status = "login_form_not_found"
                error = "Form login BLok tidak ditemukan. Cek BLOK_BASE_URL / login_path."
            else:
                page.fill(sel_user, username)
                page.fill(sel_pass, password)
                if sel_btn:
                    try:
                        with page.expect_response(
                            lambda r: "submitLogin" in r.url or r.request.method == "POST",
                            timeout=min(timeout_ms, 30000),
                        ):
                            page.locator(sel_btn).first.click()
                    except Exception:  # noqa: BLE001 — fall through to URL check
                        page.locator(sel_btn).first.click()
                page.wait_for_load_state("networkidle", timeout=timeout_ms)

            final_url = page.url
            title = page.title()
            body = ""
            try:
                body = page.inner_text("body")
            except Exception:  # noqa: BLE001
                body = ""

            if "Falsches Passwort" in body or "falsches passwort" in body.lower():
                status = "bad_password"
                error = "Login gagal: password salah."
            elif "/blok/login" in final_url and (
                page.locator('input[type="password"]').count() > 0
            ):
                status = "still_on_login"
                error = "Masih di halaman login — kredensial atau form gagal."
            elif "/blok/" in final_url and "/blok/login" not in final_url:
                logged_in = True
                status = "logged_in"
            elif "home" in final_url.lower() or "bericht" in final_url.lower():
                logged_in = True
                status = "logged_in"
            else:
                # Heuristic: password field gone → likely in app
                if page.locator('input[type="password"]').count() == 0 and "/login" not in final_url:
                    logged_in = True
                    status = "logged_in"
                else:
                    status = status if status != "failed" else "unknown"
                    if not error:
                        error = f"Login state unclear (url={final_url})."

            page.screenshot(path=str(LATEST_PNG), full_page=True)
        except Exception as e:  # noqa: BLE001 — always persist whatever we can
            error = str(e)
            status = "exception"
            try:
                final_url = page.url
                title = page.title()
                page.screenshot(path=str(LATEST_PNG), full_page=True)
            except Exception:  # noqa: BLE001
                pass
        finally:
            browser.close()

    image_exists = LATEST_PNG.is_file()
    meta: dict[str, Any] = {
        "ok": logged_in,
        "logged_in": logged_in,
        "status": status,
        "error": error,
        "login_url": login_url,
        "base_url": base_url,
        "final_url": final_url,
        "title": title,
        "taken_at": now,
        "username_hint": username[:3] + "…" if len(username) > 3 else "***",
        "image_path": "output/blok_live/latest.png" if image_exists else None,
        "image_url": "/dashboard/blok-live/latest.png" if image_exists else None,
        "meta_url": "/dashboard/api/blok/live-snapshot",
    }
    _write_meta(meta)
    return meta
