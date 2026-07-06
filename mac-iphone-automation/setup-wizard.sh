#!/bin/bash
# Wizard interaktif — jalankan di Mac setelah clone repo.
# Membantu setup izin & config Automation Hub.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"

echo "╔══════════════════════════════════════════════╗"
echo "║   Automation Hub — Setup Wizard (Mac)        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# --- Step 1: Install ---
read -r -p "Install Hub agent sekarang? [Y/n] " INSTALL
INSTALL=${INSTALL:-Y}
if [[ "$INSTALL" =~ ^[Yy]$ ]]; then
  bash "$REPO_DIR/mac/install.sh"
fi

# --- Step 2: Remote Login check ---
echo ""
echo "── Remote Login (SSH) ──"
if systemsetup -getremotelogin 2>/dev/null | grep -q "On"; then
  echo "✅ Remote Login sudah ON"
else
  echo "⚠️  Remote Login OFF"
  echo "   Buka: System Settings → General → Sharing → Remote Login → ON"
fi
HOSTNAME=$(scutil --get LocalHostName 2>/dev/null || hostname)
echo "   Hostname SSH: ${HOSTNAME}.local"

# --- Step 3: SSH key ---
echo ""
echo "── SSH Key untuk iPhone ──"
KEY="$HOME/.ssh/automation_hub"
if [[ ! -f "$KEY" ]]; then
  read -r -p "Buat SSH key baru automation_hub? [Y/n] " MKKEY
  MKKEY=${MKKEY:-Y}
  if [[ "$MKKEY" =~ ^[Yy]$ ]]; then
    ssh-keygen -t ed25519 -f "$KEY" -N "" -C "automation-hub"
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
    cat "${KEY}.pub" >> "$HOME/.ssh/authorized_keys"
    chmod 600 "$HOME/.ssh/authorized_keys"
    echo "✅ Key dibuat"
  fi
fi
if [[ -f "${KEY}.pub" ]]; then
  echo ""
  echo "📋 Copy public key ini ke iPhone Shortcuts (SSH Key field):"
  echo "────────────────────────────────────────"
  cat "${KEY}.pub"
  echo "────────────────────────────────────────"
fi

# --- Step 4: Google Sheet ID ---
echo ""
echo "── Google Sheet ──"
CONFIG="$HUB_HOME/config.env"
if [[ -f "$CONFIG" ]]; then
  read -r -p "Masukkan GOOGLE_SHEET_ID (dari URL Sheet, Enter skip): " SHEET_ID
  if [[ -n "$SHEET_ID" ]]; then
    if grep -q "^GOOGLE_SHEET_ID=" "$CONFIG"; then
      sed -i.bak "s|^GOOGLE_SHEET_ID=.*|GOOGLE_SHEET_ID=$SHEET_ID|" "$CONFIG"
    else
      echo "GOOGLE_SHEET_ID=$SHEET_ID" >> "$CONFIG"
    fi
    echo "✅ Sheet ID disimpan di $CONFIG"
  fi
fi

# --- Step 5: Webhook URL to Keychain ---
echo ""
read -r -p "Simpan Apps Script Web App URL ke Keychain? [y/N] " SAVE_WEBHOOK
if [[ "$SAVE_WEBHOOK" =~ ^[Yy]$ ]]; then
  read -r -p "Paste Web App URL: " WEBHOOK_URL
  security add-generic-password -s automation-hub -a webhook-url -w "$WEBHOOK_URL" -U 2>/dev/null \
    && echo "✅ webhook-url disimpan di Keychain" \
    || echo "⚠️  Gagal simpan Keychain"
fi

# --- Step 6: Test ---
echo ""
read -r -p "Jalankan test status sekarang? [Y/n] " TEST
TEST=${TEST:-Y}
if [[ "$TEST" =~ ^[Yy]$ ]]; then
  "$HUB_HOME/run-task.sh" status || echo "⚠️  Test gagal — cek install"
fi

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Langkah berikutnya di iPhone:               ║"
echo "╠══════════════════════════════════════════════╣"
echo "║ 1. Buat Shortcut Hub — Process iPhone Queue   ║"
echo "║ 2. Buat Shortcut Hub — WhatsApp Chat          ║"
echo "║ 3. Automation poll queue (Ask Before OFF)    ║"
echo "║ 4. SSH shortcut dengan key di atas            ║"
echo "║                                              ║"
echo "║ Panduan: docs/PERMISSIONS-AND-WORKAROUNDS.md ║"
echo "╚══════════════════════════════════════════════╝"
