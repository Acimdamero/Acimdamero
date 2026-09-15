#!/usr/bin/env bash
# Bootstrap .env dari environment secrets + jalankan API + Telegram bot.
# Dipakai agar Anda tidak perlu edit file manual.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p logs data output

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

# Tulis ulang nilai dari env secrets (Cursor / shell) jika ada
python3 - <<'PY'
from pathlib import Path
import os

import secrets

path = Path(".env")
lines = path.read_text(encoding="utf-8").splitlines()
keys = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_ALLOWED_USER_ID",
    "WHATSAPP_ALLOWED_NUMBER",
    "WAHA_BASE_URL",
    "WAHA_SESSION",
    "WAHA_API_KEY",
    "BERICHTSHEFT_API",
    "GEMINI_API_KEY",
    "DASHBOARD_TOKEN",
]
found = {k: os.environ.get(k, "").strip() for k in keys}
out = []
seen = set()
for line in lines:
    if "=" in line and not line.strip().startswith("#"):
        k = line.split("=", 1)[0].strip()
        if k in found and found[k]:
            out.append(f"{k}={found[k]}")
            seen.add(k)
            continue
    out.append(line)
for k, v in found.items():
    if v and k not in seen:
        out.append(f"{k}={v}")
# Ensure DASHBOARD_TOKEN for remote / phone access
existing_dash = ""
for line in out:
    if line.startswith("DASHBOARD_TOKEN="):
        existing_dash = line.split("=", 1)[1].strip()
        break
if not existing_dash and not found.get("DASHBOARD_TOKEN"):
    generated = secrets.token_urlsafe(32)
    if any(line.startswith("DASHBOARD_TOKEN=") for line in out):
        out = [
            f"DASHBOARD_TOKEN={generated}" if line.startswith("DASHBOARD_TOKEN=") else line
            for line in out
        ]
    else:
        out.append("")
        out.append("# Ops dashboard auth (auto-generated; do not commit)")
        out.append(f"DASHBOARD_TOKEN={generated}")
    print("DASHBOARD_TOKEN_GENERATED=yes")
else:
    print("DASHBOARD_TOKEN_GENERATED=no")
path.write_text("\n".join(out) + "\n", encoding="utf-8")
token = found.get("TELEGRAM_BOT_TOKEN") or ""
# juga baca dari file jika secret belum di env tapi sudah di .env
if not token:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            token = line.split("=", 1)[1].strip()
print("TOKEN_PRESENT=" + ("yes" if len(token) > 20 else "no"))
PY

if [[ ! -f config.yaml ]]; then
  cp config.example.yaml config.yaml
fi

if [[ ! -f berichtsheft.db ]]; then
  echo "→ init DB"
  PYTHONPATH="$ROOT" python3 -m berichtsheft init
fi

# Stop lama
for name in bericht-api bericht-bot; do
  tmux -f /exec-daemon/tmux.portal.conf has-session -t "=$name" 2>/dev/null && tmux -f /exec-daemon/tmux.portal.conf kill-session -t "$name" || true
done

# free port
if command -v lsof >/dev/null 2>&1; then
  pids=$(lsof -ti:8765 2>/dev/null || true)
  [[ -n "${pids:-}" ]] && kill $pids 2>/dev/null || true
fi
sleep 1

SESSION_API="bericht-api"
SESSION_BOT="bericht-bot"
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION_API" -c "$ROOT" -- bash -lc 'export PYTHONPATH="'"$ROOT"'"; python3 -m berichtsheft serve 2>&1 | tee logs/api.log'

sleep 2
PYTHONPATH="$ROOT" python3 -m berichtsheft telegram-check || true

TOKEN_LINE=$(grep '^TELEGRAM_BOT_TOKEN=' .env | head -1 | cut -d= -f2-)
if [[ -z "$TOKEN_LINE" || ${#TOKEN_LINE} -lt 20 ]]; then
  echo "✗ TELEGRAM_BOT_TOKEN masih kosong."
  echo "  Tambahkan secret di Cursor (prompt secrets), atau tempel token di chat — saya lanjutkan."
  echo "  API sudah jalan di tmux session: $SESSION_API (port 8765)"
  exit 2
fi

tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION_BOT" -c "$ROOT" -- bash -lc 'export PYTHONPATH="'"$ROOT"'"; set -a; source .env; set +a; python3 -m berichtsheft menu-push; python3 -m berichtsheft bot 2>&1 | tee logs/bot.log'
sleep 2
echo "✓ API: tmux $SESSION_API"
echo "✓ BOT: tmux $SESSION_BOT"
echo "→ Di HP: buka bot Telegram → kirim /start atau /menu"
tmux -f /exec-daemon/tmux.portal.conf ls
