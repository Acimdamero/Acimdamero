"""Telegram bot setup helpers."""

from __future__ import annotations

import os
from pathlib import Path

import httpx

from berichtsheft.config_loader import ROOT, load_dotenv

ENV_PATH = ROOT / ".env"
EXAMPLE_PATH = ROOT / ".env.example"


def ensure_env_file() -> bool:
    if ENV_PATH.exists():
        return False
    if EXAMPLE_PATH.exists():
        ENV_PATH.write_text(EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        return True
    return False


def check_telegram_token() -> dict:
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token.startswith("your_") or len(token) < 20:
        return {
            "ok": False,
            "error": "TELEGRAM_BOT_TOKEN belum diisi di .env",
        }
    r = httpx.get(
        f"https://api.telegram.org/bot{token}/getMe",
        timeout=15,
    )
    data = r.json()
    if not data.get("ok"):
        return {"ok": False, "error": data.get("description", "Invalid token")}
    bot = data["result"]
    return {
        "ok": True,
        "username": bot.get("username"),
        "name": bot.get("first_name"),
    }


def check_api_reachable() -> bool:
    base = os.environ.get("BERICHTSHEFT_API", "http://127.0.0.1:8765")
    try:
        r = httpx.get(f"{base}/health", timeout=3)
        return r.status_code == 200
    except httpx.HTTPError:
        return False
