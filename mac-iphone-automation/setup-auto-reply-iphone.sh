#!/bin/bash
# Setup auto-reply WA + siapkan info SSH untuk iPhone Shortcuts.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  SETUP — Auto-reply + iPhone Shortcuts                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

[[ "$(uname -s)" != "Darwin" ]] && {
  echo "❌ Jalankan di MacBook Anda."
  exit 1
}

# ── 1. Update scripts ──────────────────────────────────────────
echo "▶ [1/4] Update hub scripts..."
bash "$REPO_DIR/mac/install.sh" >/dev/null
echo "   ✅ Hub updated"

# ── 2. Cek WAHA WORKING ────────────────────────────────────────
echo "▶ [2/4] Cek WhatsApp session..."
STATUS=$(curl -sf http://127.0.0.1:3000/api/sessions/default \
  -H "X-Api-Key: ${WAHA_API_KEY:-automation-hub-test-key}" 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','UNKNOWN'))" 2>/dev/null || echo "UNREACHABLE")

if [[ "$STATUS" != "WORKING" ]]; then
  echo "   ❌ Session: $STATUS — scan QR dulu: bash pair-whatsapp.sh"
  exit 1
fi
echo "   ✅ WhatsApp WORKING"

# ── 3. Auto-reply ──────────────────────────────────────────────
echo "▶ [3/4] Aktifkan auto-reply..."
export WAHA_API_KEY="${WAHA_API_KEY:-automation-hub-test-key}"
bash "$HUB/scripts/waha-auto-reply.sh" start
echo ""
echo "   Test auto-reply:"
echo "   → Dari HP lain kirim WA ke nomor Anda: test"
echo "   → Harus dapat balasan otomatis dalam ~5 detik"
echo "   → Log: tail -f $HUB/logs/waha-inbox.log"

# ── 4. Info iPhone SSH ─────────────────────────────────────────
echo ""
echo "▶ [4/4] Siapkan iPhone Shortcuts (SSH)..."
KEY="$HOME/.ssh/automation_hub"
if [[ ! -f "${KEY}.pub" ]]; then
  ssh-keygen -t ed25519 -f "$KEY" -N "" -C "automation-hub-iphone"
  echo "   ✅ SSH key baru dibuat"
fi

HOSTNAME=$(scutil --get LocalHostName 2>/dev/null || echo "MacBook-Pro")
USER_NAME=$(whoami)

echo ""
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  IPHONE SHORTCUTS — copy data ini                      │"
echo "├─────────────────────────────────────────────────────────┤"
echo "│  Host:     ${HOSTNAME}.local"
echo "│  User:     ${USER_NAME}"
echo "│  SSH Key:  (paste di bawah ke Shortcuts)"
echo "└─────────────────────────────────────────────────────────┘"
echo ""
cat "${KEY}.pub"
echo ""
echo "Remote Login Mac:"
if systemsetup -getremotelogin 2>/dev/null | grep -q On; then
  echo "   ✅ Remote Login sudah ON"
else
  echo "   ⚠️  Aktifkan: System Settings → General → Sharing → Remote Login ON"
fi

echo ""
echo "Buat Shortcut di iPhone (Shortcuts app):"
echo "  1. + → Add Action → 'Run Script Over SSH'"
echo "  2. Host: ${HOSTNAME}.local"
echo "  3. User: ${USER_NAME}"
echo "  4. Authentication: SSH Key → paste key di atas"
echo "  5. Script:"
echo "     ~/.automation-hub/run-task.sh waha-send-name 'agwen acim damero jerman' 'Test dari iPhone'"
echo ""
echo "Panduan lengkap: iphone/INSTALL-IPHONE.md"
echo ""
echo "✅ Setup selesai!"
