"""Gemini Vision — foto → teks DE untuk Berichtsheft."""

from __future__ import annotations

import base64
import os
from typing import Optional

import httpx

from berichtsheft.ai_gemini import DEFAULT_MODEL, is_enabled as gemini_enabled
from berichtsheft.config_loader import load_config, load_dotenv


def is_vision_enabled() -> bool:
    load_dotenv()
    cfg = load_config()
    vision_cfg = cfg.get("vision") or {}
    if not vision_cfg.get("enabled", True):
        return False
    env_flag = os.environ.get("AI_VISION_ENABLED", "true").lower()
    if env_flag in ("0", "false", "no"):
        return False
    return gemini_enabled()

PROMPTS = {
    "stichpunkte": (
        "Du bist Azubi Hotelfachmann in Deutschland. Analysiere das Bild (Arbeitsfoto, "
        "Hotel, Küche, Gäste — keine personenbezogenen Namen erfinden).\n"
        "Erstelle Stichpunkte auf DEUTSCH für das Berichtsheft (Wochenbericht).\n"
        "Format: kurze Sätze mit •, formell, fachlich.\n"
        "Nur Fakten aus Bild + Hinweis des Azubis. Kein Markdown."
    ),
    "berufsschule": (
        "Du bist Azubi Hotelfachmann. Das Bild zeigt Berufsschule: Aufgaben, Unterricht, "
        "Küchenpraxis, Notizen, Tafel, Material.\n"
        "Schreibe einen DETAILLIERTEN Berichtsheft-Text auf DEUTSCH (Absätze + Stichpunkte).\n"
        "Fachbegriffe aus Gastronomie/Hotel wo passend. Keine erfundenen Namen."
    ),
    "edtime": (
        "Extrahiere Schichtplan aus EdTime-Screenshot. Antworte NUR als JSON-Array:\n"
        '[{"date":"YYYY-MM-DD","day_type":"arbeit|schule|frei","start":"HH:MM","end":"HH:MM","tags":["BRF"]}]\n'
        "Kein anderer Text."
    ),
    "lampiran": (
        "Beschreibe das Bild in 1–2 Sätzen DEUTSCH für Anhang im Berichtsheft "
        "(was ist zu sehen, welche Tätigkeit). Kein Markdown."
    ),
    "default": (
        "Beschreibe für ein deutsches Ausbildungs-Berichtsheft (Hotelfach) auf Deutsch, "
        "was auf dem Bild zu sehen ist und welche Tätigkeiten dazu passen. Formell, kurz."
    ),
}


def _detect_mode(caption: str) -> str:
    low = (caption or "").lower()
    if any(k in low for k in ("edtime", "jadwal", "schicht", "dienstplan")):
        return "edtime"
    if any(k in low for k in ("schule", "berufsschule", "unterricht", "küche", "kuche", "tugas", "soal")):
        return "berufsschule"
    if any(k in low for k in ("lampir", "anhang", "attach", "foto")):
        return "lampiran"
    if any(k in low for k in ("stichpunkt", "bullet", "laporan", "kegiatan")):
        return "stichpunkte"
    return "stichpunkte"


def analyze_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    caption: Optional[str] = None,
    mode: Optional[str] = None,
) -> tuple[str, bool, str]:
    """
    Returns (text, used_ai, mode_used).
    """
    load_dotenv()
    if not is_vision_enabled():
        return (
            "Gemini tidak aktif. Isi GEMINI_API_KEY di .env Mac.",
            False,
            mode or "default",
        )

    mode_used = mode or _detect_mode(caption or "")
    system = PROMPTS.get(mode_used, PROMPTS["default"])
    user_hint = f"\nHinweis Azubi: {caption}" if caption else ""
    prompt = system + user_hint

    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    b64 = base64.b64encode(image_bytes).decode("ascii")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    try:
        r = httpx.post(
            url,
            params={"key": api_key},
            json={
                "contents": [
                    {
                        "parts": [
                            {"inline_data": {"mime_type": mime_type, "data": b64}},
                            {"text": prompt},
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0.25, "maxOutputTokens": 4096},
            },
            timeout=90,
        )
        r.raise_for_status()
        data = r.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return ("Vision: tidak ada respons.", False, mode_used)
        parts = candidates[0].get("content", {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        return (text or "Vision: kosong.", True, mode_used)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return ("Gemini quota habis (429). Coba lagi nanti.", False, mode_used)
        return (f"Vision error: {e.response.status_code}", False, mode_used)
    except httpx.HTTPError as e:
        return (f"Vision network error: {e}", False, mode_used)
