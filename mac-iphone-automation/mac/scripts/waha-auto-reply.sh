#!/bin/bash
# Aktifkan webhook WAHA → auto-reply lokal di Mac.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${AUTOMATION_REPO:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
PORT="${WAHA_WEBHOOK_PORT:-8765}"
API_KEY="${WAHA_API_KEY:-automation-hub-test-key}"
PID_FILE="$HUB_HOME/logs/waha-webhook-relay.pid"
LOG="$HUB_HOME/logs/waha-webhook-relay.stdout.log"
COMPOSE="${WAHA_COMPOSE_FILE:-$REPO_DIR/docker/docker-compose.waha.yml}"

mkdir -p "$HUB_HOME/logs"

start_relay() {
  if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "   ✅ Webhook relay sudah jalan (PID $(cat "$PID_FILE"))"
    return 0
  fi
  export WAHA_BASE_URL="${WAHA_BASE_URL:-http://127.0.0.1:3000}"
  export WAHA_API_KEY="$API_KEY"
  export WAHA_WEBHOOK_PORT="$PORT"
  export AUTOMATION_HUB_HOME="$HUB_HOME"
  nohup python3 "$SCRIPT_DIR/waha-webhook-relay.py" >>"$LOG" 2>&1 &
  echo $! >"$PID_FILE"
  sleep 1
  curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null && echo "   ✅ Webhook relay :${PORT}" || {
    echo "   ❌ Relay gagal start — cek $LOG"
    return 1
  }
}

configure_waha_webhook() {
  export WAHA_API_KEY="$API_KEY"
  export WAHA_WEBHOOK_URL="http://host.docker.internal:${PORT}/waha/webhook"
  docker compose -f "$COMPOSE" up -d
  sleep 5
  echo "   ✅ WAHA webhook → $WAHA_WEBHOOK_URL"
}

case "${1:-start}" in
  start)
    echo "▶ Start auto-reply webhook..."
    start_relay
    configure_waha_webhook
    echo ""
    echo "✅ Auto-reply AKTIF"
    echo "   Test: kirim WA ke nomor Anda dari HP lain → dapat balasan otomatis"
    echo "   Log:  tail -f $HUB_HOME/logs/waha-inbox.log"
    ;;
  stop)
    [[ -f "$PID_FILE" ]] && kill "$(cat "$PID_FILE")" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "Webhook relay stopped"
    ;;
  status)
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "Relay: running PID $(cat "$PID_FILE")"
      curl -sf "http://127.0.0.1:${PORT}/health" && echo ""
    else
      echo "Relay: stopped"
    fi
    ;;
  *)
    echo "Usage: waha-auto-reply.sh [start|stop|status]"
    exit 1
    ;;
esac
