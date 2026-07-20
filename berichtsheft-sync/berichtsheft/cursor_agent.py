"""Cursor agent dari Telegram — local SDK via Node (@cursor/sdk)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from berichtsheft.config_loader import ROOT, load_dotenv

SCRIPT = ROOT / "scripts" / "cursor_prompt.mjs"


def is_available() -> bool:
    load_dotenv()
    key = os.environ.get("CURSOR_API_KEY", "").strip()
    return bool(key) and SCRIPT.exists()


def run_agent_prompt(
    user_text: str,
    *,
    cwd: Optional[Path] = None,
    timeout_sec: int = 300,
) -> dict[str, Any]:
    """
    Jalankan Agent.prompt lokal via Node. Butuh:
    - CURSOR_API_KEY di .env
    - npm install di project root (@cursor/sdk)
    """
    load_dotenv()
    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        return {
            "ok": False,
            "error": "CURSOR_API_KEY kosong. Buat di cursor.com/dashboard → Integrations.",
        }
    if not SCRIPT.exists():
        return {"ok": False, "error": f"Script tidak ada: {SCRIPT}"}

    work = cwd or ROOT
    model = os.environ.get("CURSOR_AGENT_MODEL", "composer-2.5")
    env = os.environ.copy()
    env["CURSOR_API_KEY"] = api_key
    env["CURSOR_AGENT_CWD"] = str(work)
    env["CURSOR_AGENT_MODEL"] = model

    prompt = (
        "Du arbeitest am Projekt berichtsheft-sync (Azubi Hotelfachmann, BLok, Telegram).\n"
        "Antworte auf Deutsch oder Indonesisch wie der Azubi fragt.\n"
        "Keine destruktiven Git-Befehle ohne explizite Anweisung.\n\n"
        f"Aufgabe:\n{user_text}"
    )

    try:
        proc = subprocess.run(
            ["node", str(SCRIPT)],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env,
            cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Timeout setelah {timeout_sec}s"}
    except FileNotFoundError:
        return {"ok": False, "error": "Node.js tidak ditemukan. Install Node 18+."}

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[:2000]
        return {"ok": False, "error": err or f"exit {proc.returncode}"}

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"ok": True, "result": proc.stdout.strip()}

    data.setdefault("ok", True)
    return data
