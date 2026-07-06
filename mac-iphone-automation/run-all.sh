#!/bin/bash
# JALANKAN SEMUA — satu perintah untuk setup lengkap Mac + WAHA + test.
# Usage: bash run-all.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
API_KEY="${WAHA_API_KEY:-automation-hub-test-key}"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     AUTOMATION HUB — RUN ALL (full setup)                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

[[ "$(uname -s)" != "Darwin" ]] && {
  echo "⚠️  Script ini untuk Mac. Jalankan di Terminal MacBook Anda."
  exit 1
}

# ── 1. Docker Desktop ──────────────────────────────────────────
echo "▶ [1/8] Buka Docker Desktop..."
if ! docker info >/dev/null 2>&1; then
  open -a Docker
  echo "   Menunggu Docker siap..."
  for i in $(seq 1 90); do
    docker info >/dev/null 2>&1 && break
    printf "."
    sleep 2
  done
  echo ""
fi
docker info >/dev/null 2>&1 || { echo "❌ Docker gagal start. Buka Docker Desktop manual."; exit 1; }
echo "   ✅ Docker siap"

# ── 2. Install Hub ───────────────────────────────────────────
echo "▶ [2/8] Install Hub agent..."
bash "$REPO_DIR/mac/install.sh"

# ── 3. Enable autostart ──────────────────────────────────────
echo "▶ [3/8] Aktifkan autostart Docker+WAHA..."
bash "$REPO_DIR/enable-docker-autostart.sh" 2>/dev/null || true

# ── 4. Start WAHA ────────────────────────────────────────────
echo "▶ [4/8] Start WAHA container..."
export WAHA_API_KEY="$API_KEY"
export AUTOMATION_REPO="$REPO_DIR"
docker compose -f "$REPO_DIR/docker/docker-compose.waha.yml" up -d
sleep 10
docker ps | grep -q automation-hub-waha || { echo "❌ WAHA container gagal"; exit 1; }
echo "   ✅ WAHA container running"

# ── 5. Start WhatsApp session ────────────────────────────────
echo "▶ [5/8] Pair WhatsApp (WAHA)..."
if bash "$REPO_DIR/pair-whatsapp.sh" "agwen acim damero jerman" \
  "🤖 Test Automation Hub — semua sistem jalan otomatis ✅" 2>/dev/null; then
  WA_CONNECTED=1
else
  WA_CONNECTED=0
fi

# ── 6. SSH key untuk iPhone ────────────────────────────────────
echo "▶ [6/8] SSH key untuk iPhone..."
KEY="$HOME/.ssh/automation_hub"
if [[ -f "${KEY}.pub" ]]; then
  echo "   ✅ SSH key ada"
  echo "   📋 Public key (paste ke iPhone Shortcuts):"
  cat "${KEY}.pub"
else
  echo "   ⚠️  SSH key belum ada — jalankan: bash install-all.sh"
fi

# ── 7. Verify ────────────────────────────────────────────────
echo "▶ [7/8] Verifikasi..."
bash "$REPO_DIR/verify-install.sh" || true

# ── 8. Test kirim WA (jika terhubung) ─────────────────────────
echo "▶ [8/8] Test kirim WhatsApp..."
if [[ "${WA_CONNECTED:-0}" == "1" ]]; then
  echo "   ✅ Pesan test sudah dikirim via pair-whatsapp.sh"
else
  echo ""
  echo "   ⚠️  WhatsApp belum terhubung — jalankan:"
  echo "   bash pair-whatsapp.sh"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ RUN ALL SELESAI                                       ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Hub:    ~/.automation-hub/run-task.sh status            ║"
echo "║  WAHA:   http://localhost:3000/dashboard                 ║"
echo "║  iPhone: iphone/INSTALL-IPHONE.md                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
