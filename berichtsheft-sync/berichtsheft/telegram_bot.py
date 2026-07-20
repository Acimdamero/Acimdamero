"""Telegram long-polling bot → local API."""

from __future__ import annotations

import base64
import os
import time

import httpx

from berichtsheft.config_loader import ROOT, load_config, load_dotenv

API_BASE = os.environ.get("BERICHTSHEFT_API", "http://127.0.0.1:8765")
AI_TIMEOUT = 330
UPLOAD_TIMEOUT = 300
AUDIT_TIMEOUT = 420
CHAT_ID_FILE = ROOT / "data" / "telegram_chat_id.txt"


def _allowed(user_id: int) -> bool:
    raw = os.environ.get("TELEGRAM_ALLOWED_USER_ID", "").strip()
    if not raw:
        return True
    return str(user_id) in raw.split(",")


def _remember_chat(chat_id: int) -> None:
    CHAT_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_ID_FILE.write_text(str(chat_id))


def _saved_chat_id() -> int | None:
    if not CHAT_ID_FILE.is_file():
        return None
    try:
        return int(CHAT_ID_FILE.read_text().strip())
    except ValueError:
        return None


def _send(token: str, chat_id: int, text: str) -> None:
    httpx.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text[:4000]},
        timeout=30,
    )


def _reminder_config() -> dict:
    cfg = load_config()
    tg = cfg.get("telegram") or {}
    rem = tg.get("reminders") or {}
    return {
        "enabled": rem.get("enabled", True),
        "interval_hours": int(rem.get("interval_hours", 12)),
        "only_if_issues": rem.get("only_if_issues", True),
    }


def _week_offsets(arg: str) -> str:
    """Return offsets query string for /audit/weeks."""
    low = (arg or "").lower().strip()
    if low in ("lalu", "last", "-1"):
        return "-1"
    if low in ("ini", "this", "0", "sekarang"):
        return "0"
    if low in ("depan", "next", "+1", "1"):
        return "1"
    if low in ("", "semua", "all"):
        cfg = load_config()
        tg = cfg.get("telegram") or {}
        offs = tg.get("week_offsets", [-1, 0, 1])
        return ",".join(str(x) for x in offs)
    return low.replace(" ", ",")


def _audit_offsets() -> str:
    cfg = load_config()
    tg = cfg.get("telegram") or {}
    offs = tg.get("audit_offsets", [-2, -1, 0, 1])
    return ",".join(str(x) for x in offs)


def _download_photo(token: str, file_id: str) -> tuple[bytes, str]:
    meta = httpx.get(
        f"https://api.telegram.org/bot{token}/getFile",
        params={"file_id": file_id},
        timeout=30,
    ).json()
    if not meta.get("ok"):
        raise RuntimeError("getFile gagal")
    path = meta["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{token}/{path}"
    data = httpx.get(url, timeout=60).content
    mime = "image/jpeg"
    if path.lower().endswith(".png"):
        mime = "image/png"
    elif path.lower().endswith(".webp"):
        mime = "image/webp"
    return data, mime


def _handle_photo(token: str, chat_id: int, msg: dict) -> None:
    photos = msg.get("photo") or []
    if not photos:
        return
    caption = (msg.get("caption") or "").strip()
    file_id = photos[-1]["file_id"]
    try:
        raw, mime = _download_photo(token, file_id)
    except Exception as e:
        _send(token, chat_id, f"⚠ Gagal unduh foto: {e}")
        return

    payload = {
        "image_base64": base64.b64encode(raw).decode("ascii"),
        "caption": caption or None,
        "mime_type": mime,
    }
    try:
        with httpx.Client(base_url=API_BASE, timeout=120) as client:
            r = client.post("/vision/analyze", json=payload)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:500] if e.response else str(e)
        _send(token, chat_id, f"⚠ Vision: {detail}")
        return
    except httpx.HTTPError as e:
        _send(token, chat_id, f"⚠ API tidak reachable: {e}")
        return

    mode = data.get("mode", "?")
    text = data.get("text", "")
    prefix = "✓ Foto dianalisis"
    if data.get("used_ai"):
        prefix += " (Gemini Vision)"
    lines = [f"{prefix} — mode: {mode}", f"Tanggal: {data.get('date')}"]
    if data.get("log_id"):
        lines.append("✓ Masuk work log")
    if data.get("attachment_id"):
        aid = data["attachment_id"]
        lines.append(f"📎 Lampiran #{aid} disimpan di Mac")
        lines.append(f"→ /lampirkan {aid} untuk upload ke BLok")
    if data.get("hint_edtime"):
        lines.append(f"\n{data['hint_edtime']}")
    short = text[:3500] + ("…" if len(text) > 3500 else "")
    lines.append(f"\n{short}")
    _send(token, chat_id, "\n".join(lines))


def _help_text(user_id: int) -> str:
    uid_hint = (
        f"\n\n🆔 User ID Anda: {user_id}\n"
        f"Tambahkan ke .env:\nTELEGRAM_ALLOWED_USER_ID={user_id}"
    )
    return (
        "Berichtsheft-Sync\n\n"
        "📝 Log kerja:\n"
        "• Kirim teks biasa = log\n"
        "• /log … — catatan eksplisit\n\n"
        "📷 Foto (Gemini Vision):\n"
        "• Kirim foto + caption (stichpunkte, berufsschule, edtime, lampiran)\n"
        "• /foto — bantuan foto\n\n"
        "📎 Upload ke BLok (Entwicklungsportfolio):\n"
        "• /lampiran [tanggal] — daftar foto di database\n"
        "• /lampirkan ID — upload + lampir ke hari foto\n"
        "• /lampirkan semua — semua foto hari ini\n\n"
        "📋 Draft & BLok:\n"
        "• /selesai [ringkasan] — draft + dry-run\n"
        "• /ok — setujui + isi BLok live\n"
        "• /ubah … — koreksi (satu pesan)\n"
        "• /status — ringkasan hari\n\n"
        "📊 Audit & pengingat:\n"
        "• /minggu — cek minggu lalu/ini/depan\n"
        "• /minggu lalu | depan | ini\n"
        "• /audit — scan lebih luas (kosong, draft, foto)\n"
        "  Bot mengingatkan otomatis jika ada yang kurang\n\n"
        "🤖 Cursor: /ai perintah … (1–5 menit)\n"
        + uid_hint
    )


def _format_lampiran(data: dict) -> str:
    lines = [f"📎 Lampiran {data.get('date')}", ""]
    atts = data.get("attachments") or []
    if not atts:
        lines.append("Tidak ada foto. Kirim foto + caption ke bot.")
        return "\n".join(lines)
    for a in atts:
        st = a.get("blok_status") or "belum"
        icon = "✓" if st == "bound" else ("↑" if st == "uploaded" else "○")
        cap = (a.get("caption") or "")[:40]
        lines.append(
            f"{icon} #{a['id']} — {st}"
            + (f" — {cap}" if cap else "")
        )
    lines.append("\n/lampirkan ID — upload ke BLok Dokumentenablage + einbinden")
    return "\n".join(lines)


def _handle_command(token: str, chat_id: int, user_id: int, text: str) -> None:
    if not _allowed(user_id):
        _send(token, chat_id, "⛔ User tidak diizinkan. Set TELEGRAM_ALLOWED_USER_ID di .env")
        return

    _remember_chat(chat_id)

    parts = text.strip().split()
    cmd = parts[0].lower()
    arg = text.strip()[len(parts[0]) :].strip() if len(parts) > 1 else ""

    with httpx.Client(base_url=API_BASE, timeout=60) as client:
        if cmd in ("/start", "/help"):
            _send(token, chat_id, _help_text(user_id))
        elif cmd == "/foto":
            _send(
                token,
                chat_id,
                "📷 Kirim foto + caption:\n\n"
                "• stichpunkte / kegiatan → Stichpunkte DE\n"
                "• berufsschule / schule → laporan sekolah rinci\n"
                "• edtime / jadwal → extract JSON shift\n"
                "• lampiran / anhang → deskripsi untuk lampiran\n\n"
                "Setelah foto: /lampirkan ID untuk upload ke BLok.\n"
                "Video belum didukung.",
            )
        elif cmd == "/log":
            if not arg:
                _send(token, chat_id, "Format: /log aktivitas Anda")
                return
            r = client.post("/log", json={"text": arg})
            _send(token, chat_id, f"✓ Tersimpan ({r.json().get('date')})")
        elif cmd == "/lampiran":
            params = {}
            if arg:
                params["date"] = arg.split()[0]
            r = client.get("/attachments", params=params)
            _send(token, chat_id, _format_lampiran(r.json()))
        elif cmd == "/lampirkan":
            ids: list[int] = []
            iso = None
            if not arg or arg.lower() in ("semua", "all"):
                pass
            else:
                tokens = arg.split()
                for t in tokens:
                    if t.lower() in ("semua", "all"):
                        continue
                    if "-" in t and len(t) == 10:
                        iso = t
                        continue
                    try:
                        ids.append(int(t))
                    except ValueError:
                        iso = t
            _send(token, chat_id, "⏳ Upload ke BLok Dokumentenablage… (±1–2 menit/foto)")
            payload: dict = {"bind": True}
            if ids:
                payload["attachment_ids"] = ids
            if iso:
                payload["date"] = iso
            try:
                with httpx.Client(base_url=API_BASE, timeout=UPLOAD_TIMEOUT) as up:
                    r = up.post("/attachments/upload-blok", json=payload)
                    r.raise_for_status()
                    data = r.json()
            except httpx.HTTPStatusError as e:
                detail = ""
                try:
                    detail = e.response.json().get("detail", "")
                except Exception:
                    detail = e.response.text[:300] if e.response else str(e)
                _send(token, chat_id, f"⚠ Upload gagal: {detail}")
                return
            except httpx.HTTPError as e:
                _send(token, chat_id, f"⚠ Timeout/error: {e}")
                return
            lines = [f"✓ Upload BLok ({data.get('date')})", ""]
            for res in data.get("results") or []:
                if res.get("skipped"):
                    lines.append(f"⏭ #{res['attachment_id']} sudah dilampirkan")
                elif res.get("error"):
                    lines.append(f"⚠ #{res['attachment_id']}: {res['error'][:200]}")
                else:
                    bound = " + einbinden" if res.get("bound") else ""
                    lines.append(
                        f"✓ #{res['attachment_id']} → {res.get('blok_filename', '?')}{bound}"
                    )
            _send(token, chat_id, "\n".join(lines))
        elif cmd == "/minggu":
            offsets = _week_offsets(arg)
            _send(token, chat_id, f"⏳ Scan BLok minggu ({offsets})…")
            try:
                with httpx.Client(base_url=API_BASE, timeout=AUDIT_TIMEOUT) as aud:
                    r = aud.get("/audit/weeks", params={"offsets": offsets})
                    r.raise_for_status()
                    preview = r.json().get("preview", "Selesai.")
            except httpx.HTTPStatusError as e:
                detail = ""
                try:
                    detail = e.response.json().get("detail", "")
                except Exception:
                    detail = str(e)
                _send(token, chat_id, f"⚠ /minggu gagal: {detail}")
                return
            except httpx.HTTPError as e:
                _send(token, chat_id, f"⚠ Timeout: {e}")
                return
            _send(token, chat_id, preview)
        elif cmd == "/audit":
            offsets = _audit_offsets()
            _send(token, chat_id, f"⏳ Audit BLok ({offsets})… bisa beberapa menit")
            try:
                with httpx.Client(base_url=API_BASE, timeout=AUDIT_TIMEOUT) as aud:
                    r = aud.get("/audit/weeks", params={"offsets": offsets})
                    r.raise_for_status()
                    preview = r.json().get("preview", "Selesai.")
            except httpx.HTTPStatusError as e:
                detail = ""
                try:
                    detail = e.response.json().get("detail", "")
                except Exception:
                    detail = str(e)
                _send(token, chat_id, f"⚠ /audit gagal: {detail}")
                return
            except httpx.HTTPError as e:
                _send(token, chat_id, f"⚠ Timeout: {e}")
                return
            _send(token, chat_id, preview)
        elif cmd == "/selesai":
            r = client.post("/finish", json={"summary": arg or None})
            data = r.json()
            _send(token, chat_id, data.get("preview", "Selesai."))
            w = data.get("worker")
            if w:
                if w.get("output"):
                    _send(token, chat_id, f"📁 Dry-run: {w['output']}")
                elif w.get("saved") is not None:
                    note = w.get("note", "")
                    _send(
                        token,
                        chat_id,
                        f"{'✓' if w.get('saved') else '⚠'} BLok live: {note}",
                    )
                elif w.get("skipped"):
                    _send(token, chat_id, f"⏭ Worker skip: {w.get('reason', '')}")
        elif cmd == "/status":
            r = client.get("/status")
            d = r.json()
            _send(
                token,
                chat_id,
                f"Tanggal: {d['date']}\nShift: {d['has_shift']}\nLog: {d['log_count']}\n"
                f"Foto: {d.get('attachment_count', 0)}\n"
                f"Draft: {d['draft_status']}\nApproval: {d['approval']}",
            )
        elif cmd == "/ok":
            r = client.post("/approve")
            data = r.json()
            _send(token, chat_id, f"✓ Disetujui {data.get('date')}")
            w = data.get("worker")
            if w:
                if w.get("output"):
                    _send(token, chat_id, f"📁 Dry-run: {w['output']}")
                elif w.get("saved") is not None:
                    _send(token, chat_id, f"{'✓' if w.get('saved') else '⚠'} BLok: {w.get('note', '')}")
        elif cmd == "/ai":
            if not arg:
                _send(
                    token,
                    chat_id,
                    "Format: /ai perintah Anda (bahasa biasa)\n\n"
                    "Contoh:\n/ai ringkas log hari ini ke Stichpunkte DE\n\n"
                    "⏳ Bisa 1–5 menit. Mac + CURSOR_API_KEY harus aktif.",
                )
                return
            _send(token, chat_id, "⏳ Cursor agent jalan… (bisa beberapa menit)")
            try:
                with httpx.Client(base_url=API_BASE, timeout=AI_TIMEOUT) as ai_client:
                    r = ai_client.post("/ai", json={"text": arg})
                    r.raise_for_status()
                    data = r.json()
            except httpx.HTTPStatusError as e:
                detail = ""
                try:
                    detail = e.response.json().get("detail", "")
                except Exception:
                    detail = e.response.text[:400] if e.response else str(e)
                _send(token, chat_id, f"⚠ /ai gagal: {detail}")
                return
            except httpx.HTTPError as e:
                _send(token, chat_id, f"⚠ API timeout/error: {e}")
                return
            result = (data.get("result") or "")[:3800]
            status = data.get("status", "done")
            _send(token, chat_id, f"✓ Cursor ({status})\n\n{result or '(kosong)'}")
        elif cmd == "/ubah":
            if not arg:
                _send(
                    token,
                    chat_id,
                    "❌ Teks koreksi harus SEKALIGUS dengan /ubah\n\n"
                    "Contoh (satu pesan):\n"
                    "/ubah Bitte formell auf Deutsch mit Hotelfachbegriffen\n\n"
                    "Bukan /ubah di pesan terpisah.\n"
                    "Perlu Gemini? Isi GEMINI_API_KEY di .env Mac",
                )
                return
            try:
                r = client.post("/correct", json={"text": arg})
                r.raise_for_status()
                data = r.json()
                preview = data.get("preview", "Diperbarui.")
                if data.get("draft", {}).get("ai_polish"):
                    preview = "✨ KI (Gemini)\n\n" + preview
                _send(token, chat_id, preview)
            except httpx.HTTPStatusError as e:
                detail = ""
                try:
                    detail = e.response.json().get("detail", "")
                except Exception:
                    detail = str(e)
                _send(token, chat_id, f"⚠ {detail}")
        else:
            _send(token, chat_id, "Perintah tidak dikenal. /help")


def _maybe_send_reminder(token: str) -> None:
    rem = _reminder_config()
    if not rem["enabled"]:
        return
    chat_id = _saved_chat_id()
    if not chat_id:
        return
    try:
        with httpx.Client(base_url=API_BASE, timeout=AUDIT_TIMEOUT) as client:
            r = client.get(
                "/audit/weeks",
                params={"offsets": _week_offsets("")},
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        print(f"Reminder skip: {e}")
        return

    report = data.get("report") or {}
    total = report.get("summary", {}).get("total_issues", 0)
    if rem["only_if_issues"] and total == 0:
        return

    preview = data.get("preview", "")
    if preview:
        _send(token, chat_id, f"🔔 Pengingat Berichtsheft\n\n{preview}")


def run_polling() -> None:
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN kosong di .env")

    rem = _reminder_config()
    interval = max(1, rem["interval_hours"]) * 3600
    last_reminder = 0.0

    print(f"Bot polling… API={API_BASE} (reminder every {rem['interval_hours']}h)")
    offset = 0
    while True:
        try:
            if time.time() - last_reminder >= interval:
                _maybe_send_reminder(token)
                last_reminder = time.time()

            r = httpx.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"timeout": 30, "offset": offset},
                timeout=35,
            )
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                text = msg.get("text") or ""
                chat = msg.get("chat") or {}
                user = msg.get("from") or {}
                uid = user.get("id", 0)
                cid = chat.get("id")

                if not _allowed(uid):
                    if text or msg.get("photo") or msg.get("video"):
                        _send(token, cid, "⛔ User tidak diizinkan.")
                    continue

                if msg.get("video"):
                    _send(
                        token,
                        cid,
                        "🎬 Video belum didukung — kirim foto + caption.\n"
                        "Contoh caption: stichpunkte hari ini",
                    )
                    continue

                if msg.get("photo"):
                    _handle_photo(token, cid, msg)
                    continue

                if not text:
                    continue
                if text.startswith("/"):
                    _handle_command(token, cid, uid, text)
                else:
                    _handle_command(token, cid, uid, f"/log {text}")
        except httpx.HTTPError as e:
            print(f"Network error: {e}")
            time.sleep(5)
        except KeyboardInterrupt:
            print("Bot stopped.")
            break
