#!/usr/bin/env bash
# Mac always-on hub: serve (0.0.0.0:8765) + optional bot + Cloudflare Tunnel.
# Writes public URL to data/remote_hub_url.txt (gitignored).
#
# Usage:
#   ./scripts/start_remote_hub.sh              # API + tunnel
#   ./scripts/start_remote_hub.sh --bot        # + Telegram bot
#   ./scripts/start_remote_hub.sh --bot both   # + Telegram + WhatsApp
#   ./scripts/start_remote_hub.sh --stop       # stop hub processes
#   START_BOT=1 ./scripts/start_remote_hub.sh
#
# Requires: DASHBOARD_TOKEN or SYNC_TOKEN in .env (wajib untuk remote/tunnel).
# Docs: docs/REMOTE_ALWAYS_ON.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DO_BOT=0
BOT_MODE="telegram"
DO_STOP=0
for arg in "$@"; do
  case "$arg" in
    --bot) DO_BOT=1 ;;
    --stop) DO_STOP=1 ;;
    telegram|whatsapp|both) BOT_MODE="$arg"; DO_BOT=1 ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
  esac
done
if [[ "${START_BOT:-0}" == "1" || "${START_BOT:-}" == "true" ]]; then
  DO_BOT=1
fi

mkdir -p logs data output
PID_API="logs/hub-api.pid"
PID_BOT="logs/hub-bot.pid"
PID_WA="logs/hub-wa.pid"
PID_TUNNEL="logs/hub-tunnel.pid"
LOG_API="logs/hub-api.log"
LOG_BOT="logs/hub-bot.log"
LOG_WA="logs/hub-wa.log"
LOG_TUNNEL="logs/hub-tunnel.log"
URL_FILE="data/remote_hub_url.txt"

stop_pidfile() {
  local f="$1"
  if [[ -f "$f" ]]; then
    local old
    old="$(cat "$f" 2>/dev/null || true)"
    if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
      echo "→ stop PID $old ($f)"
      kill "$old" 2>/dev/null || true
      sleep 1
      kill -0 "$old" 2>/dev/null && kill -9 "$old" 2>/dev/null || true
    fi
    rm -f "$f"
  fi
}

stop_all() {
  stop_pidfile "$PID_TUNNEL"
  stop_pidfile "$PID_BOT"
  stop_pidfile "$PID_WA"
  stop_pidfile "$PID_API"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti:8765 2>/dev/null || true)"
    if [[ -n "${pids:-}" ]]; then
      echo "→ free port 8765: $pids"
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
    fi
  fi
  echo "✓ hub stopped"
}

if [[ "$DO_STOP" -eq 1 ]]; then
  stop_all
  exit 0
fi

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "✗ .env dibuat dari .env.example — isi DASHBOARD_TOKEN dulu, lalu jalankan ulang."
  exit 1
fi

# shellcheck disable=SC1091
set -a
source .env
set +a

TOKEN="${DASHBOARD_TOKEN:-}"
if [[ -z "$TOKEN" ]]; then
  TOKEN="${SYNC_TOKEN:-}"
fi
if [[ -z "$TOKEN" ]]; then
  echo "✗ DASHBOARD_TOKEN atau SYNC_TOKEN wajib di .env sebelum tunnel publik."
  echo "  Generate: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
  exit 1
fi

if [[ ! -f config.yaml ]]; then
  cp config.example.yaml config.yaml
  echo "→ config.yaml dari contoh (host 0.0.0.0)"
fi

# Ensure bind 0.0.0.0 for tunnel (best-effort; config.example already uses it)
if grep -qE '^\s*host:\s*"127\.0\.0\.1"' config.yaml 2>/dev/null; then
  echo "⚠ config.yaml host=127.0.0.1 — tunnel butuh 0.0.0.0. Mengganti…"
  if command -v sed >/dev/null 2>&1; then
    sed -i.bak 's/host: "127.0.0.1"/host: "0.0.0.0"/' config.yaml || true
  fi
fi

if [[ ! -f berichtsheft.db ]]; then
  echo "→ init database…"
  PYTHONPATH="$ROOT" python3 -m berichtsheft init
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "✗ cloudflared tidak ditemukan."
  echo "  Mac: brew install cloudflare/cloudflare/cloudflared"
  echo "  Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
  exit 1
fi

stop_all

echo "→ start API serve (0.0.0.0:8765)…"
nohup env PYTHONPATH="$ROOT" python3 -m berichtsheft serve >"$LOG_API" 2>&1 &
echo $! >"$PID_API"
sleep 2

if ! curl -sf "http://127.0.0.1:8765/health" >/dev/null 2>&1; then
  echo "✗ API belum sehat — lihat $LOG_API"
  exit 1
fi
echo "✓ API healthy"

if [[ "$DO_BOT" -eq 1 ]]; then
  case "$BOT_MODE" in
    telegram|both)
      if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
        echo "⚠ TELEGRAM_BOT_TOKEN kosong — skip Telegram bot"
      else
        PYTHONPATH="$ROOT" python3 -m berichtsheft menu-push >/dev/null 2>&1 || true
        echo "→ start Telegram bot…"
        nohup env PYTHONPATH="$ROOT" bash -lc 'set -a; source .env; set +a; python3 -m berichtsheft bot' >"$LOG_BOT" 2>&1 &
        echo $! >"$PID_BOT"
      fi
      ;;
  esac
  case "$BOT_MODE" in
    whatsapp|both)
      if [[ -z "${WHATSAPP_ALLOWED_NUMBER:-}" ]]; then
        echo "⚠ WHATSAPP_ALLOWED_NUMBER kosong — skip WhatsApp bot"
      else
        echo "→ start WhatsApp bot…"
        nohup env PYTHONPATH="$ROOT" bash -lc 'set -a; source .env; set +a; python3 -m berichtsheft wa-bot' >"$LOG_WA" 2>&1 &
        echo $! >"$PID_WA"
      fi
      ;;
  esac
fi

echo "→ start cloudflared quick tunnel…"
: >"$LOG_TUNNEL"
nohup cloudflared tunnel --url "http://127.0.0.1:8765" >"$LOG_TUNNEL" 2>&1 &
echo $! >"$PID_TUNNEL"

PUBLIC_URL=""
for _ in $(seq 1 40); do
  sleep 1
  # Match trycloudflare.com / cfargotunnel hosts from cloudflared log
  PUBLIC_URL="$(
    grep -Eo 'https://[a-zA-Z0-9.-]+\.(trycloudflare\.com|cfargotunnel\.com)' "$LOG_TUNNEL" 2>/dev/null \
      | head -1 || true
  )"
  if [[ -n "$PUBLIC_URL" ]]; then
    break
  fi
done

if [[ -z "$PUBLIC_URL" ]]; then
  echo "✗ Gagal membaca public URL dari $LOG_TUNNEL (tunnel mungkin masih mulai)."
  echo "  Cek log, lalu isi manual data/remote_hub_url.txt"
  exit 1
fi

printf '%s\n' "$PUBLIC_URL" >"$URL_FILE"

# Best-effort: seed sync_config remote_api_url (no token written)
python3 - <<PY
import json
from pathlib import Path
url = Path("data/remote_hub_url.txt").read_text(encoding="utf-8").strip().rstrip("/")
path = Path("data/sync_config.json")
cfg = {}
if path.is_file():
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        cfg = {}
if not isinstance(cfg, dict):
    cfg = {}
cfg["remote_api_url"] = url
# never write tokens here
for k in ("remote_token", "token", "DASHBOARD_TOKEN", "SYNC_TOKEN"):
    cfg.pop(k, None)
path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"→ sync_config remote_api_url={url}")
PY

DASH_URL="${PUBLIC_URL}/dashboard?token=${TOKEN}"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Mac hub ALWAYS-ON (demo / permanente di Mac, bukan Cloud)"
echo "═══════════════════════════════════════════════════════════"
echo "  Public API:  $PUBLIC_URL"
echo "  Phone dash:  $DASH_URL"
echo "  URL file:    $URL_FILE"
echo "  Token:       (dari .env DASHBOARD_TOKEN / SYNC_TOKEN — jangan share log)"
echo ""
echo "  Cloud .env:"
echo "    BERICHTSHEFT_REMOTE_API=$PUBLIC_URL"
echo "    BERICHTSHEFT_REMOTE_TOKEN=<same-as-DASHBOARD_TOKEN>"
echo "    BERICHTSHEFT_API=$PUBLIC_URL"
echo ""
echo "  Stop: ./scripts/start_remote_hub.sh --stop"
echo "  Docs: docs/REMOTE_ALWAYS_ON.md"
echo "═══════════════════════════════════════════════════════════"
