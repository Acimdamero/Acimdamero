#!/bin/bash
# Pair WhatsApp via WAHA — start container, buka QR, tunggu WORKING, test kirim.
# Usage:
#   bash pair-whatsapp.sh
#   bash pair-whatsapp.sh "agwen acim damero jerman" "Pesan test"

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
API_KEY="${WAHA_API_KEY:-automation-hub-test-key}"
BASE_URL="${WAHA_BASE_URL:-http://127.0.0.1:3000}"
SESSION="${WAHA_SESSION:-default}"
CONTACT_NAME="${1:-}"
TEST_MSG="${2:-🤖 Test Automation Hub — WhatsApp otomatis berhasil ✅}"
POLL_MAX="${WAHA_PAIR_TIMEOUT:-180}"

api() {
  curl -sf "${HEADERS[@]}" "$@"
}

HEADERS=(-H "X-Api-Key: $API_KEY")

session_status() {
  api "$BASE_URL/api/sessions/$SESSION" 2>/dev/null \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status','UNKNOWN'))" 2>/dev/null \
    || echo "UNREACHABLE"
}

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     WHATSAPP PAIR — WAHA Automation Hub                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Docker + WAHA ───────────────────────────────────────────
echo "▶ [1/4] Start Docker + WAHA..."
if [[ "$(uname -s)" == "Darwin" ]]; then
  export AUTOMATION_REPO="$REPO_DIR"
  export OPEN_WAHA_DASHBOARD=0
  bash "$REPO_DIR/mac/scripts/docker-autostart.sh" 2>/dev/null || {
    open -a Docker 2>/dev/null || true
    for i in $(seq 1 90); do docker info >/dev/null 2>&1 && break; sleep 2; done
    export WAHA_API_KEY="$API_KEY"
    docker compose -f "$REPO_DIR/docker/docker-compose.waha.yml" up -d
    sleep 8
  }
else
  if ! docker info >/dev/null 2>&1; then
    sudo docker info >/dev/null 2>&1 || { echo "❌ Docker tidak jalan"; exit 1; }
  fi
  export WAHA_API_KEY="$API_KEY"
  docker compose -f "$REPO_DIR/docker/docker-compose.waha.yml" up -d 2>/dev/null \
    || sudo docker compose -f "$REPO_DIR/docker/docker-compose.waha.yml" up -d
  sleep 8
fi
echo "   ✅ WAHA container running"

# ── 2. Start / restart session ─────────────────────────────────
echo "▶ [2/4] Start session WhatsApp..."
api -X POST "$BASE_URL/api/sessions/stop" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$SESSION\"}" >/dev/null 2>&1 || true
sleep 2
api -X POST "$BASE_URL/api/sessions/start" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$SESSION\",\"config\":{\"engine\":\"WEBJS\"}}" >/dev/null 2>&1 || true
sleep 5

STATUS=$(session_status)
echo "   Status awal: $STATUS"

# ── 3. QR pairing ──────────────────────────────────────────────
echo "▶ [3/4] Pair WhatsApp (scan QR)..."
if [[ "$STATUS" != "WORKING" ]]; then
  echo ""
  echo "   ┌─────────────────────────────────────────────────┐"
  echo "   │  SCAN QR SEKARANG (sekali saja):                │"
  echo "   │                                                 │"
  echo "   │  1. Buka: http://localhost:3000/dashboard       │"
  echo "   │  2. Login: admin / change-me                    │"
  echo "   │  3. Sessions → default → QR                     │"
  echo "   │  4. iPhone: WhatsApp → Linked Devices → Scan   │"
  echo "   └─────────────────────────────────────────────────┘"
  echo ""

  if [[ "$(uname -s)" == "Darwin" ]]; then
    open "http://localhost:3000/dashboard" 2>/dev/null || true
  fi

  echo "   Menunggu pairing (max ${POLL_MAX}s)..."
  for ((i=1; i<=POLL_MAX; i++)); do
    STATUS=$(session_status)
    if [[ "$STATUS" == "WORKING" ]]; then
      echo ""
      echo "   ✅ WhatsApp terhubung! ($i detik)"
      break
    fi
    if (( i % 15 == 0 )); then
      echo "   ... masih $STATUS (${i}s) — scan QR di dashboard"
    fi
    sleep 1
  done
fi

STATUS=$(session_status)
if [[ "$STATUS" != "WORKING" ]]; then
  echo ""
  echo "❌ WhatsApp belum WORKING (status: $STATUS)"
  echo "   Buka http://localhost:3000/dashboard → scan QR → jalankan lagi:"
  echo "   bash pair-whatsapp.sh"
  exit 1
fi

# ── 4. Test kirim ─────────────────────────────────────────────
echo "▶ [4/4] Test kirim pesan..."
RUN_TASK="$HUB_HOME/run-task.sh"
[[ -x "$RUN_TASK" ]] || RUN_TASK="$REPO_DIR/mac/scripts/run-task.sh"

if [[ -n "$CONTACT_NAME" ]]; then
  if "$RUN_TASK" waha-send-name "$CONTACT_NAME" "$TEST_MSG"; then
    echo "   ✅ Pesan terkirim ke: $CONTACT_NAME"
  else
    echo "   ⚠️  Kirim gagal — cek nama kontak di WhatsApp"
    exit 1
  fi
else
  echo "   ✅ Session WORKING — siap kirim!"
  echo ""
  echo "   Test manual:"
  echo "   ~/.automation-hub/run-task.sh waha-send-name \"nama kontak\" \"pesan\""
  echo "   ~/.automation-hub/run-task.sh waha-send 6281234567890 \"pesan\""
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ WHATSAPP OTOMATIS AKTIF                               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
