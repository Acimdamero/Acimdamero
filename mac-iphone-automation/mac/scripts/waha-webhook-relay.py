#!/usr/bin/env python3
"""Webhook lokal WAHA — log pesan masuk + auto-reply ke pengirim."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone

PORT = int(os.environ.get("WAHA_WEBHOOK_PORT", "8765"))
BASE_URL = os.environ.get("WAHA_BASE_URL", "http://127.0.0.1:3000")
API_KEY = os.environ.get("WAHA_API_KEY", "automation-hub-test-key")
SESSION = os.environ.get("WAHA_SESSION", "default")
HUB_HOME = os.environ.expanduser(os.environ.get("AUTOMATION_HUB_HOME", "~/.automation-hub"))
LOG_FILE = os.path.join(HUB_HOME, "logs", "waha-inbox.log")
AUTO_REPLY = os.environ.get("WAHA_AUTO_REPLY", "1") == "1"
REPLY_PREFIX = os.environ.get("WAHA_REPLY_PREFIX", "🤖 Hub auto-reply")


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def send_text(chat_id: str, text: str) -> bool:
    payload = json.dumps({"session": SESSION, "chatId": chat_id, "text": text}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/sendText",
        data=payload,
        headers={"Content-Type": "application/json", "X-Api-Key": API_KEY},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            log(f"SENT {chat_id}: {text[:80]}")
            return resp.status == 200 or resp.status == 201
    except urllib.error.HTTPError as e:
        log(f"SEND FAIL {chat_id}: HTTP {e.code} {e.read()[:200]}")
        return False
    except Exception as e:
        log(f"SEND FAIL {chat_id}: {e}")
        return False


def build_reply(sender: str, body: str) -> str:
    text = (body or "").strip().lower()
    if text in ("status", "ping", "test"):
        try:
            out = subprocess.check_output(
                [os.path.join(HUB_HOME, "run-task.sh"), "status"],
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
            return f"{REPLY_PREFIX}\n\nMac status:\n{out.decode()[:500]}"
        except Exception:
            return f"{REPLY_PREFIX}\n\nMac hub aktif ✅ (status detail gagal dibaca)"
    if text in ("help", "bantuan", "?"):
        return (
            f"{REPLY_PREFIX}\n\nPerintah:\n"
            "• status — info Mac\n"
            "• test — echo balasan\n"
            "• pesan apa saja — dapat balasan otomatis"
        )
    if text == "test":
        return f"{REPLY_PREFIX}\n\nTest auto-reply OK ✅"
    return f"{REPLY_PREFIX}\n\nTerima: «{body[:200]}»\nBalas otomatis dari Automation Hub."


def handle_event(data: dict) -> None:
    event = data.get("event") or data.get("type") or ""
    if event not in ("message", "message.any", "message.create"):
        return

    payload = data.get("payload") or data
    if payload.get("fromMe") is True:
        return

    chat_id = payload.get("from") or payload.get("chatId") or ""
    body = payload.get("body") or payload.get("text") or ""
    if not chat_id or not str(body).strip():
        return

    log(f"IN  {chat_id}: {body[:200]}")
    if AUTO_REPLY:
        reply = build_reply(chat_id, str(body))
        send_text(chat_id, reply)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        if self.path in ("/health", "/waha/webhook", "/waha/webhook/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true,"service":"waha-webhook-relay"}')
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            data = {}
        try:
            handle_event(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        except Exception as e:
            log(f"ERROR handling webhook: {e}")
            self.send_response(500)
            self.end_headers()


def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    log(f"Webhook relay listening on :{PORT} → WAHA {BASE_URL}")
    log(f"Auto-reply: {'ON' if AUTO_REPLY else 'OFF'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
