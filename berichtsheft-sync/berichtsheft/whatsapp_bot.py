"""WhatsApp bot via WAHA — nomor personal Anda → API Berichtsheft lokal."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

from berichtsheft.config_loader import ROOT, load_dotenv
from berichtsheft.telegram_bot import (
    BTN_AI,
    BTN_AUDIT,
    BTN_FOTO,
    BTN_HELP,
    BTN_LAMPIRAN,
    BTN_LOG,
    BTN_MENU,
    BTN_MINGGU,
    BTN_OK,
    BTN_SELESAI,
    BTN_STATUS,
    BTN_UBAH,
    _help_text,
    _resolve_menu_text,
)

API_BASE = os.environ.get("BERICHTSHEFT_API", "http://127.0.0.1:8765")
AI_TIMEOUT = 330
UPLOAD_TIMEOUT = 300
AUDIT_TIMEOUT = 420
CHAT_ID_FILE = ROOT / "data" / "whatsapp_chat_id.txt"
SEEN_FILE = ROOT / "data" / "whatsapp_seen_ids.json"


def _waha_base() -> str:
    return os.environ.get("WAHA_BASE_URL", "http://127.0.0.1:3000").rstrip("/")


def _waha_session() -> str:
    return os.environ.get("WAHA_SESSION", "default").strip() or "default"


def _waha_headers() -> dict[str, str]:
    key = os.environ.get("WAHA_API_KEY", "").strip()
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-Api-Key"] = key
    return headers


def normalize_chat_id(raw: str) -> str:
    """628xxx atau +62… → 628xxx@c.us"""
    s = (raw or "").strip().replace(" ", "").replace("-", "")
    if not s:
        return ""
    if "@" in s:
        return s
    if s.startswith("+"):
        s = s[1:]
    if s.startswith("0"):
        s = "62" + s[1:]
    return f"{s}@c.us"


def _allowed_chat_ids() -> set[str]:
    raw = os.environ.get("WHATSAPP_ALLOWED_NUMBER", "").strip()
    if not raw:
        return set()
    out: set[str] = set()
    for part in raw.split(","):
        cid = normalize_chat_id(part)
        if cid:
            out.add(cid)
            # juga izinkan tanpa @c.us untuk cek fleksibel
            out.add(cid.split("@")[0])
    return out


def _is_allowed(chat_id: str) -> bool:
    allowed = _allowed_chat_ids()
    if not allowed:
        # kosong = tolak semua sampai diisi (lebih aman untuk WA personal)
        return False
    phone = (chat_id or "").split("@")[0]
    return chat_id in allowed or phone in allowed


def _remember_chat(chat_id: str) -> None:
    CHAT_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_ID_FILE.write_text(normalize_chat_id(chat_id), encoding="utf-8")


def _saved_chat_id() -> str | None:
    if not CHAT_ID_FILE.is_file():
        return None
    return CHAT_ID_FILE.read_text(encoding="utf-8").strip() or None


def menu_text() -> str:
    return (
        "📒 *Berichtsheft WhatsApp*\n\n"
        "Balas dengan nomor / teks tombol / perintah:\n\n"
        f"1 · {BTN_LOG}\n"
        f"2 · {BTN_SELESAI}\n"
        f"3 · {BTN_STATUS}\n"
        f"4 · {BTN_OK}\n"
        f"5 · {BTN_MINGGU}\n"
        f"6 · {BTN_AUDIT}\n"
        f"7 · {BTN_FOTO}\n"
        f"8 · {BTN_LAMPIRAN}\n"
        f"9 · {BTN_UBAH}\n"
        f"0 · {BTN_HELP}\n"
        f"m · {BTN_MENU}\n\n"
        "Atau ketik langsung catatan kerja (jadi /log).\n"
        "Contoh: `/selesai` · `/ok` · `/minggu`"
    )


NUMBER_MAP = {
    "1": BTN_LOG,
    "2": BTN_SELESAI,
    "3": BTN_STATUS,
    "4": BTN_OK,
    "5": BTN_MINGGU,
    "6": BTN_AUDIT,
    "7": BTN_FOTO,
    "8": BTN_LAMPIRAN,
    "9": BTN_UBAH,
    "0": BTN_HELP,
    "m": BTN_MENU,
    "menu": BTN_MENU,
}


def send_text(chat_id: str, text: str) -> dict:
    chat_id = normalize_chat_id(chat_id)
    # WhatsApp plain text — hilangkan markdown * untuk kompatibilitas
    body = text.replace("*", "")
    r = httpx.post(
        f"{_waha_base()}/api/sendText",
        headers=_waha_headers(),
        json={
            "session": _waha_session(),
            "chatId": chat_id,
            "text": body[:4000],
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json() if r.content else {"ok": True}


def check_waha() -> dict:
    load_dotenv()
    try:
        r = httpx.get(
            f"{_waha_base()}/api/sessions",
            headers=_waha_headers(),
            timeout=10,
        )
        if r.status_code >= 400:
            return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        sessions = r.json()
        return {
            "ok": True,
            "base": _waha_base(),
            "session": _waha_session(),
            "sessions": sessions,
            "allowed": bool(_allowed_chat_ids()),
            "allowed_numbers": sorted(_allowed_chat_ids()),
        }
    except httpx.HTTPError as e:
        return {"ok": False, "error": str(e)}


def _api_send_reply(chat_id: str, text: str) -> None:
    try:
        send_text(chat_id, text)
    except httpx.HTTPError as e:
        print(f"WA send gagal: {e}")


def _handle_command_via_api(chat_id: str, user_label: str, text: str) -> None:
    """Reuse logika yang sama dengan Telegram lewat HTTP API lokal."""
    if not _is_allowed(chat_id):
        _api_send_reply(
            chat_id,
            "⛔ Nomor tidak diizinkan.\n"
            "Isi WHATSAPP_ALLOWED_NUMBER=628… di .env Mac, lalu restart wa-bot.",
        )
        return

    _remember_chat(chat_id)
    parts = text.strip().split()
    cmd = parts[0].lower() if parts else ""
    arg = text.strip()[len(parts[0]) :].strip() if len(parts) > 1 else ""

    with httpx.Client(base_url=API_BASE, timeout=60) as client:
        if cmd in ("/start", "/help", "/menu", "menu", "0"):
            _api_send_reply(chat_id, menu_text() + "\n\n" + _help_text(0).replace("🆔 User ID Anda: 0\nTambahkan ke .env:\nTELEGRAM_ALLOWED_USER_ID=0", f"📱 Chat: {chat_id}"))
            return

        # Map ke endpoint yang sama seperti telegram_bot
        if cmd == "/foto":
            _api_send_reply(
                chat_id,
                "📷 Kirim foto + caption ke WhatsApp bot ini.\n"
                "Caption: stichpunkte / berufsschule / edtime / lampiran",
            )
            return
        if cmd == "/log":
            if not arg:
                _api_send_reply(chat_id, "Format: /log aktivitas Anda\natau ketik teks biasa.")
                return
            r = client.post("/log", json={"text": arg})
            _api_send_reply(chat_id, f"✓ Tersimpan ({r.json().get('date')})")
            return
        if cmd == "/lampiran":
            params = {}
            if arg:
                params["date"] = arg.split()[0]
            r = client.get("/attachments", params=params)
            data = r.json()
            lines = [f"📎 Lampiran {data.get('date')}", ""]
            atts = data.get("attachments") or []
            if not atts:
                lines.append("Tidak ada foto.")
            for a in atts:
                lines.append(f"#{a['id']} — {a.get('blok_status') or 'belum'}")
            _api_send_reply(chat_id, "\n".join(lines))
            return
        if cmd == "/lampirkan":
            _api_send_reply(chat_id, "⏳ Upload ke BLok…")
            payload: dict = {}
            if arg.strip().lower() in ("semua", "all", "*"):
                pass
            elif arg.strip().isdigit():
                payload["attachment_ids"] = [int(arg.strip())]
            else:
                _api_send_reply(chat_id, "Format: /lampirkan ID atau /lampirkan semua")
                return
            try:
                with httpx.Client(base_url=API_BASE, timeout=UPLOAD_TIMEOUT) as up:
                    r = up.post("/attachments/upload-blok", json=payload)
                    r.raise_for_status()
                    _api_send_reply(chat_id, r.json().get("preview") or "✓ Upload selesai")
            except httpx.HTTPError as e:
                _api_send_reply(chat_id, f"⚠ Upload gagal: {e}")
            return
        if cmd == "/minggu":
            _api_send_reply(chat_id, "📅 Scan minggu…")
            try:
                with httpx.Client(base_url=API_BASE, timeout=AUDIT_TIMEOUT) as aud:
                    r = aud.get("/audit/weeks", params={"offsets": "-1,0,1"})
                    r.raise_for_status()
                    _api_send_reply(chat_id, r.json().get("preview") or "OK")
            except httpx.HTTPError as e:
                _api_send_reply(chat_id, f"⚠ /minggu gagal: {e}")
            return
        if cmd == "/audit":
            _api_send_reply(chat_id, "🔍 Audit…")
            try:
                with httpx.Client(base_url=API_BASE, timeout=AUDIT_TIMEOUT) as aud:
                    r = aud.get("/audit/weeks", params={"offsets": "-2,-1,0,1"})
                    r.raise_for_status()
                    _api_send_reply(chat_id, r.json().get("preview") or "OK")
            except httpx.HTTPError as e:
                _api_send_reply(chat_id, f"⚠ /audit gagal: {e}")
            return
        if cmd == "/selesai":
            _api_send_reply(chat_id, "⏳ Membuat draft…")
            try:
                r = client.post("/finish", json={"summary": arg or None})
                r.raise_for_status()
                data = r.json()
                _api_send_reply(chat_id, data.get("preview") or "✓ Draft siap")
            except httpx.HTTPError as e:
                _api_send_reply(chat_id, f"⚠ /selesai gagal: {e}")
            return
        if cmd == "/status":
            r = client.get("/status")
            _api_send_reply(chat_id, r.json().get("preview") or json.dumps(r.json(), ensure_ascii=False)[:1500])
            return
        if cmd == "/ok":
            _api_send_reply(chat_id, "⏳ /ok — isi BLok…")
            try:
                r = client.post("/approve", json={})
                r.raise_for_status()
                _api_send_reply(chat_id, r.json().get("preview") or "✓ Disetujui")
            except httpx.HTTPError as e:
                _api_send_reply(chat_id, f"⚠ /ok gagal: {e}")
            return
        if cmd == "/ai":
            if not arg:
                _api_send_reply(chat_id, "Format: /ai perintah Anda")
                return
            _api_send_reply(chat_id, "🤖 Cursor agent…")
            try:
                with httpx.Client(base_url=API_BASE, timeout=AI_TIMEOUT) as ai:
                    r = ai.post("/ai", json={"text": arg})
                    r.raise_for_status()
                    _api_send_reply(chat_id, r.json().get("preview") or "OK")
            except httpx.HTTPError as e:
                _api_send_reply(chat_id, f"⚠ /ai gagal: {e}")
            return
        if cmd == "/ubah":
            if not arg:
                _api_send_reply(
                    chat_id,
                    "Format satu pesan:\n/ubah Bitte formell auf Deutsch …",
                )
                return
            try:
                r = client.post("/correct", json={"text": arg})
                r.raise_for_status()
                _api_send_reply(chat_id, r.json().get("preview") or "Diperbarui.")
            except httpx.HTTPError as e:
                _api_send_reply(chat_id, f"⚠ {e}")
            return

        _api_send_reply(chat_id, "Perintah tidak dikenal. Ketik menu atau /help")


def handle_incoming_text(chat_id: str, text: str, *, from_me: bool = False) -> None:
    if from_me:
        return
    text = (text or "").strip()
    if not text:
        return

    # nomor menu
    low = text.lower().strip()
    if low in NUMBER_MAP:
        text = NUMBER_MAP[low]

    action = _resolve_menu_text(text)
    if action == "/menu" or text == BTN_MENU:
        _handle_command_via_api(chat_id, chat_id, "/menu")
        return
    if action and action.startswith("__prompt_"):
        # kirim prompt lewat WA (reuse teks telegram prompt)
        # _prompt_for butuh token telegram — kirim manual
        if action == "__prompt_log__":
            _api_send_reply(
                chat_id,
                "📝 Kirim teks kegiatan sekarang (satu pesan).\n"
                "Contoh: Buffet auffüllen und Gäste begrüßen",
            )
        elif action == "__prompt_ubah__":
            _api_send_reply(
                chat_id,
                "✏️ Contoh:\n/ubah Bitte formell auf Deutsch mit Hotelfachbegriffen",
            )
        elif action == "__prompt_ai__":
            _api_send_reply(chat_id, "🤖 Format: /ai perintah Anda")
        return
    if action and action.startswith("/"):
        _handle_command_via_api(chat_id, chat_id, action)
        return

    if text.startswith("/"):
        _handle_command_via_api(chat_id, chat_id, text)
    else:
        _handle_command_via_api(chat_id, chat_id, f"/log {text}")


def parse_waha_webhook(payload: dict) -> tuple[str, str, bool] | None:
    """Extract chat_id, text, from_me dari event WAHA."""
    event = payload.get("event") or payload.get("type") or ""
    data = payload.get("payload") or payload.get("data") or payload
    if isinstance(data, dict) and "payload" in data and event:
        data = data.get("payload") or data

    # Bentuk umum WAHA message
    msg = data if isinstance(data, dict) else {}
    if "body" not in msg and isinstance(payload.get("payload"), dict):
        msg = payload["payload"]

    text = (
        msg.get("body")
        or msg.get("text")
        or (msg.get("message") or {}).get("text")
        or ""
    )
    if isinstance(text, dict):
        text = text.get("body") or text.get("text") or ""

    chat_id = (
        msg.get("from")
        or msg.get("chatId")
        or (msg.get("chat") or {}).get("id")
        or ""
    )
    from_me = bool(msg.get("fromMe") or msg.get("from_me"))
    if not chat_id or not text:
        return None
    return str(chat_id), str(text), from_me


def _load_seen() -> set[str]:
    if not SEEN_FILE.is_file():
        return set()
    try:
        return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return set()


def _save_seen(seen: set[str]) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    # keep last 500
    items = list(seen)[-500:]
    SEEN_FILE.write_text(json.dumps(items), encoding="utf-8")


def poll_once(seen: set[str]) -> set[str]:
    """Poll pesan dari chat yang diizinkan (fallback tanpa webhook)."""
    allowed = [c for c in _allowed_chat_ids() if "@" in c]
    if not allowed:
        return seen
    session = _waha_session()
    for chat_id in allowed:
        try:
            r = httpx.get(
                f"{_waha_base()}/api/{session}/chats/{chat_id}/messages",
                headers=_waha_headers(),
                params={"limit": 20},
                timeout=30,
            )
            if r.status_code >= 400:
                continue
            messages = r.json()
            if not isinstance(messages, list):
                messages = messages.get("messages") or messages.get("data") or []
            for msg in reversed(messages):
                mid = str(msg.get("id") or msg.get("key", {}).get("id") or "")
                if mid and mid in seen:
                    continue
                text = msg.get("body") or msg.get("text") or ""
                from_me = bool(msg.get("fromMe"))
                if mid:
                    seen.add(mid)
                if text and not from_me:
                    handle_incoming_text(chat_id, str(text), from_me=False)
        except httpx.HTTPError as e:
            print(f"poll {chat_id}: {e}")
    return seen


def push_menu() -> None:
    load_dotenv()
    chat_id = _saved_chat_id() or next(iter([c for c in _allowed_chat_ids() if "@" in c]), None)
    if not chat_id:
        raise SystemExit(
            "Belum ada chat. Isi WHATSAPP_ALLOWED_NUMBER=628… di .env lalu "
            "kirim pesan ke nomor WA yang ter-pair WAHA, atau set nomor itu."
        )
    send_text(chat_id, menu_text())
    print(f"✓ Menu dikirim ke {chat_id}")


def run_polling(interval_sec: float = 3.0) -> None:
    load_dotenv()
    if not _allowed_chat_ids():
        raise SystemExit(
            "WHATSAPP_ALLOWED_NUMBER kosong di .env — isi nomor WA Anda (628…)"
        )
    status = check_waha()
    if not status.get("ok"):
        raise SystemExit(f"WAHA tidak siap: {status.get('error')}")
    print(
        f"WA bot polling… WAHA={_waha_base()} session={_waha_session()} "
        f"API={API_BASE}"
    )
    print("Webhook alternatif: POST /whatsapp/webhook ke API (port 8765)")
    seen = _load_seen()
    try:
        send_text(
            next(c for c in _allowed_chat_ids() if "@" in c),
            "✓ Berichtsheft WhatsApp bot online.\n\n" + menu_text(),
        )
    except Exception as e:
        print(f"⚠ Gagal kirim menu awal: {e}")

    while True:
        try:
            seen = poll_once(seen)
            _save_seen(seen)
        except Exception as e:
            print(f"poll error: {e}")
        time.sleep(interval_sec)
