#!/usr/bin/env bash
# Jalankan Berichtsheft-Sync lokal (API + bot Telegram) — tanpa Cloud.
# Usage: ./scripts/run_local.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "→ .env dibuat dari .env.example — isi TELEGRAM_BOT_TOKEN dulu, lalu jalankan ulang."
  exit 1
fi

# shellcheck disable=SC1091
set -a
source .env
set +a

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "✗ TELEGRAM_BOT_TOKEN kosong di .env"
  exit 1
fi

if [[ ! -f config.yaml ]]; then
  cp config.example.yaml config.yaml
  echo "→ config.yaml dari contoh"
fi

if [[ ! -f berichtsheft.db ]]; then
  echo "→ init database…"
  python3 -m berichtsheft init
fi

mkdir -p output logs
PID_API="logs/api.pid"
PID_BOT="logs/bot.pid"
LOG_API="logs/api.log"
LOG_BOT="logs/bot.log"

stop_old() {
  for f in "$PID_API" "$PID_BOT"; do
    if [[ -f "$f" ]]; then
      old=$(cat "$f" || true)
      if [[ -n "$old" ]] && kill -0 "$old" 2>/dev/null; then
        echo "→ stop PID $old"
        kill "$old" 2>/dev/null || true
        sleep 1
      fi
      rm -f "$f"
    fi
  done
  # fallback: proses lama di port 8765
  if command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -ti:8765 2>/dev/null || true)
    if [[ -n "${pids:-}" ]]; then
      echo "→ free port 8765: $pids"
      kill $pids 2>/dev/null || true
      sleep 1
    fi
  fi
}

stop_old

echo "→ start API (serve)…"
nohup python3 -m berichtsheft serve >"$LOG_API" 2>&1 &
echo $! >"$PID_API"
sleep 2

if ! python3 -m berichtsheft telegram-check; then
  echo "⚠ API/token check gagal — lihat $LOG_API"
fi

echo "→ push menu ke Telegram (jika chat sudah pernah /start)…"
python3 -m berichtsheft menu-push || true

echo "→ start bot (foreground — Ctrl+C untuk stop)…"
python3 -m berichtsheft bot
