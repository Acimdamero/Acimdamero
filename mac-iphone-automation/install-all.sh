#!/bin/bash
# Instalasi lengkap Automation Hub — jalankan di Mac.
# Usage: bash install-all.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "⚠️  Script ini untuk macOS. Jalankan di MacBook Anda."
  exit 1
fi

echo "╔══════════════════════════════════════════════╗"
echo "║   Automation Hub — Full Install (Mac)        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 1. Hub agent
echo "==> [1/5] Install Hub agent..."
bash "$REPO_DIR/mac/install.sh"

# 2. SSH key for iPhone
echo ""
echo "==> [2/5] SSH key untuk iPhone..."
KEY="$HOME/.ssh/automation_hub"
if [[ ! -f "$KEY" ]]; then
  ssh-keygen -t ed25519 -f "$KEY" -N "" -C "automation-hub"
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"
  touch "$HOME/.ssh/authorized_keys"
  chmod 600 "$HOME/.ssh/authorized_keys"
  grep -qF "$(cat "${KEY}.pub")" "$HOME/.ssh/authorized_keys" 2>/dev/null \
    || cat "${KEY}.pub" >> "$HOME/.ssh/authorized_keys"
  echo "✅ SSH key dibuat"
fi
echo ""
echo "📋 Public key — paste ke iPhone Shortcuts (SSH Key):"
echo "────────────────────────────────────────"
cat "${KEY}.pub"
echo "────────────────────────────────────────"

# 3. Remote Login reminder
echo ""
echo "==> [3/5] Remote Login..."
if systemsetup -getremotelogin 2>/dev/null | grep -q "On"; then
  echo "✅ Remote Login ON"
else
  echo "⚠️  Nyalakan: System Settings → General → Sharing → Remote Login"
fi
HOSTNAME=$(scutil --get LocalHostName 2>/dev/null || hostname)
echo "   Hostname iPhone SSH: ${HOSTNAME}.local"

# 4. Docker + WAHA
echo ""
echo "==> [4/5] Docker + WAHA..."
if ! command -v docker >/dev/null 2>&1; then
  echo "⚠️  Docker belum terinstall. Install Docker Desktop:"
  echo "   https://www.docker.com/products/docker-desktop/"
else
  if docker info >/dev/null 2>&1; then
    docker compose -f "$REPO_DIR/docker/docker-compose.waha.yml" up -d
    echo "✅ WAHA starting → http://localhost:3000"
    echo "   Scan QR: WhatsApp → Linked Devices → Link a Device"
  else
    echo "⚠️  Buka Docker Desktop dulu, lalu jalankan:"
    echo "   docker compose -f $REPO_DIR/docker/docker-compose.waha.yml up -d"
  fi
fi

# 5. Test
echo ""
echo "==> [5/5] Test Hub..."
"$HUB_HOME/run-task.sh" status || true

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅ Instalasi Mac selesai                    ║"
echo "╠══════════════════════════════════════════════╣"
echo "║ iPhone — buka Shortcuts, buat:               ║"
echo "║  • Hub — Status Mac (SSH)                    ║"
echo "║  • Hub — Execute Command                     ║"
echo "║  • Hub — WhatsApp Test (Open URL wa.me)      ║"
echo "║                                              ║"
echo "║ Test WA (Mac harus WAHA + QR scan):          ║"
echo "║  ~/.automation-hub/run-task.sh waha-status  ║"
echo "║  ~/.automation-hub/run-task.sh waha-send-name\\"
echo "║    \"agwen acim damero jerman\" \"Test Hub\"     ║"
echo "║                                              ║"
echo "║ Panduan: iphone/INSTALL-IPHONE.md            ║"
echo "╚══════════════════════════════════════════════╝"
