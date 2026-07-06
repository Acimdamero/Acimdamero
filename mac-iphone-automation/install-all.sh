#!/bin/bash
# Instalasi lengkap — non-interactive, Mac atau Linux.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
OS="$(uname -s)"

echo "╔══════════════════════════════════════════════╗"
echo "║   Automation Hub — Full Install              ║"
echo "╚══════════════════════════════════════════════╝"

# 1. Hub agent
echo "==> [1/6] Hub agent..."
bash "$REPO_DIR/mac/install.sh"

# 2. Config defaults
echo "==> [2/6] Config..."
grep -q '^WAHA_API_KEY=' "$HUB_HOME/config.env" 2>/dev/null || echo 'WAHA_API_KEY=automation-hub-test-key' >> "$HUB_HOME/config.env"
sed -i.bak 's|^# WAHA_API_KEY=.*|WAHA_API_KEY=automation-hub-test-key|' "$HUB_HOME/config.env" 2>/dev/null || true
sed -i.bak 's|^WHATSAPP_BACKEND=.*|WHATSAPP_BACKEND=waha|' "$HUB_HOME/config.env" 2>/dev/null || true

# 3. SSH key
echo "==> [3/6] SSH key..."
KEY="$HOME/.ssh/automation_hub"
if [[ ! -f "$KEY" ]]; then
  mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
  ssh-keygen -t ed25519 -f "$KEY" -N "" -C "automation-hub" -q
  touch "$HOME/.ssh/authorized_keys" && chmod 600 "$HOME/.ssh/authorized_keys"
  grep -qF "$(cat "${KEY}.pub")" "$HOME/.ssh/authorized_keys" 2>/dev/null || cat "${KEY}.pub" >> "$HOME/.ssh/authorized_keys"
  echo "✅ SSH key: $KEY"
fi

# 4. Remote Login (macOS only)
if [[ "$OS" == "Darwin" ]]; then
  echo "==> [4/6] Remote Login..."
  systemsetup -getremotelogin 2>/dev/null | grep -q On && echo "✅ Remote Login ON" || echo "⚠️  Enable Remote Login in System Settings"
else
  echo "==> [4/6] Remote Login skipped (not macOS)"
fi

# 5. Docker + WAHA
echo "==> [5/6] Docker + WAHA..."
DOCKER_CMD="docker"
if ! docker info >/dev/null 2>&1; then
  if sudo docker info >/dev/null 2>&1; then
    DOCKER_CMD="sudo docker"
  elif [[ "$OS" != "Darwin" ]]; then
    if ! command -v docker >/dev/null; then
      sudo apt-get update -qq && sudo apt-get install -y -qq docker.io docker-compose-v2 2>/dev/null || true
    fi
    if ! pgrep -x dockerd >/dev/null 2>&1; then
      sudo dockerd >/tmp/dockerd-hub.log 2>&1 &
      sleep 4
    fi
    docker info >/dev/null 2>&1 || DOCKER_CMD="sudo docker"
  fi
fi

if $DOCKER_CMD info >/dev/null 2>&1; then
  export WAHA_API_KEY="${WAHA_API_KEY:-automation-hub-test-key}"
  $DOCKER_CMD compose -f "$REPO_DIR/docker/docker-compose.waha.yml" up -d 2>&1 || \
    $DOCKER_CMD compose -f "$REPO_DIR/docker/docker-compose.waha.yml" pull 2>&1 && \
    $DOCKER_CMD compose -f "$REPO_DIR/docker/docker-compose.waha.yml" up -d 2>&1 || true

  sleep 5
  if $DOCKER_CMD ps --format '{{.Names}}' 2>/dev/null | grep -q automation-hub-waha; then
    echo "✅ WAHA container running → http://localhost:3000"
  else
    echo "⚠️  WAHA container not running — open Docker Desktop on Mac and retry"
  fi
else
  echo "⚠️  Docker not available — install Docker Desktop on Mac"
fi

# 6. Test
echo "==> [6/6] Tests..."
"$HUB_HOME/run-task.sh" status 2>&1 | tail -3 || true
bash "$REPO_DIR/verify-install.sh" 2>&1 || true

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Install selesai                             ║"
echo "╠══════════════════════════════════════════════╣"
echo "║ Mac: scan QR → http://localhost:3000         ║"
echo "║ iPhone: iphone/INSTALL-IPHONE.md             ║"
echo "║ Test WA:                                     ║"
echo "║  bash enable-docker-autostart.sh  (otomatis) ║"
echo "║  ~/.automation-hub/run-task.sh waha-send-name\\"
echo "║    \"agwen acim damero jerman\" \"Test Hub\"       ║"
echo "╚══════════════════════════════════════════════╝"
