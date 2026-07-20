"""Optional Gemini polish for Berichtsheft text (Fase A)."""

from __future__ import annotations

import os
from typing import Optional

import httpx

from berichtsheft.config_loader import load_dotenv

DEFAULT_MODEL = "gemini-2.5-flash"


def is_enabled() -> bool:
    load_dotenv()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    enabled = os.environ.get("AI_POLISH_ENABLED", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    return bool(key) and enabled


def polish_german(
    taetigkeiten: str,
    instruction: Optional[str] = None,
    *,
    context: Optional[str] = None,
) -> tuple[str, bool]:
    """
    Returns (text, used_ai).
    If no API key, returns original text unchanged.
    """
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or not is_enabled():
        return taetigkeiten, False

    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip()
    user_instruction = instruction or (
        "Formuliere den Text formell auf Deutsch für ein Berichtsheft "
        "(Hotelfachmann/-frau). Verwende Fachbegriffe aus Hotel und Ausbildung. "
        "Nur Fakten aus dem Original, nichts erfinden."
    )
    prompt = f"""Du bist Ausbilder-Sprachhilfe für ein deutsches Berichtsheft.

Aufgabe: {user_instruction}

Kontext Schicht:
{context or '—'}

Originaltext:
---
{taetigkeiten}
---

Gib NUR den fertigen Berichtsheft-Text auf Deutsch zurück (mit Absätzen).
Keine Erklärung, kein Markdown."""

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    try:
        r = httpx.post(
            url,
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return taetigkeiten, False
        parts = candidates[0].get("content", {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        return (text or taetigkeiten), True
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RuntimeError(
                "Gemini quota habis (429). Cek https://aistudio.google.com — tunggu atau upgrade."
            ) from e
        return taetigkeiten, False
    except httpx.HTTPError:
        return taetigkeiten, False
