#!/usr/bin/env bash
# Jalankan Berichtsheft-Sync lokal (API + bot Telegram dan/atau WhatsApp) — tanpa Cloud.
# Usage:
#   ./scripts/run_local.sh              # Telegram (default)
#   ./scripts/run_local.sh telegram
#   ./scripts/run_local.sh whatsapp     # butuh WAHA + WHATSAPP_ALLOWED_NUMBER
#   ./scripts/run_local.sh both
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="${1:-telegram}"

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "→ .env dibuat dari .env.example — isi token/nomor dulu, lalu jalankan ulang."
  exit 1
fi

# shellcheck disable=SC1091
set -a
source .env
set +a

need_telegram=0
need_whatsapp=0
case "$MODE" in
  telegram) need_telegram=1 ;;
  whatsapp) need_whatsapp=1 ;;
  both) need_telegram=1; need_whatsapp=1 ;;
  *)
    echo "Usage: $0 [telegram|whatsapp|both]"
    exit 1
    ;;
esac

if [[ "$need_telegram" -eq 1 && -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "✗ TELEGRAM_BOT_TOKEN kosong di .env"
  exit 1
fi

if [[ "$need_whatsapp" -eq 1 && -z "${WHATSAPP_ALLOWED_NUMBER:-}" ]]; then
  echo "✗ WHATSAPP_ALLOWED_NUMBER kosong di .env — isi nomor WA Anda (628…)"
  echo "  Lihat docs/WHATSAPP.md"
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
PID_WA="logs/wa-bot.pid"
LOG_API="logs/api.log"
LOG_BOT="logs/bot.log"
LOG_WA="logs/wa-bot.log"

stop_old() {
  for f in "$PID_API" "$PID_BOT" "$PID_WA"; do
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

if [[ "$need_telegram" -eq 1 ]]; then
  if ! python3 -m berichtsheft telegram-check; then
    echo "⚠ API/token check gagal — lihat $LOG_API"
  fi
  echo "→ push menu ke Telegram (jika chat sudah pernah /start)…"
  python3 -m berichtsheft menu-push || true
fi

if [[ "$need_whatsapp" -eq 1 ]]; then
  if ! python3 -m berichtsheft wa-check; then
    echo "⚠ WAHA check gagal — jalankan Docker WAHA dulu (lihat docs/WHATSAPP.md)"
  fi
  python3 -m berichtsheft wa-menu-push || true
fi

if [[ "$MODE" == "whatsapp" ]]; then
  echo "→ start WhatsApp bot (foreground — Ctrl+C untuk stop)…"
  python3 -m berichtsheft wa-bot
elif [[ "$MODE" == "both" ]]; then
  echo "→ start WhatsApp bot (background)…"
  nohup python3 -m berichtsheft wa-bot >"$LOG_WA" 2>&1 &
  echo $! >"$PID_WA"
  echo "→ start Telegram bot (foreground — Ctrl+C untuk stop)…"
  python3 -m berichtsheft bot
else
  echo "→ start Telegram bot (foreground — Ctrl+C untuk stop)…"
  python3 -m berichtsheft bot
fi
