#!/bin/bash
# Verifikasi instalasi Automation Hub — jalankan setelah install.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
PASS=0
FAIL=0

ok()  { echo "✅ $1"; PASS=$((PASS+1)); }
bad() { echo "❌ $1"; FAIL=$((FAIL+1)); }

echo "=== Automation Hub Verify ==="
echo ""

# 1. Hub files
[[ -x "$HUB_HOME/run-task.sh" ]] && ok "run-task.sh" || bad "run-task.sh missing"
[[ -f "$HUB_HOME/scripts/waha-send.sh" ]] && ok "waha-send.sh" || bad "waha-send.sh missing"
[[ -f "$HUB_HOME/config.env" ]] && ok "config.env" || bad "config.env missing"

# 2. run-task help
if "$HUB_HOME/run-task.sh" help >/dev/null 2>&1; then
  ok "run-task help"
else
  bad "run-task help"
fi

# 3. status
if "$HUB_HOME/run-task.sh" status >/dev/null 2>&1; then
  ok "run-task status"
else
  bad "run-task status"
fi

# 4. Docker
DOCKER_CMD="docker"
if ! docker info >/dev/null 2>&1; then
  sudo docker info >/dev/null 2>&1 && DOCKER_CMD="sudo docker" || true
fi
if $DOCKER_CMD info >/dev/null 2>&1; then
  ok "docker daemon"
else
  bad "docker daemon (buka Docker Desktop di Mac)"
fi

# 5. WAHA container
if $DOCKER_CMD ps --format '{{.Names}}' 2>/dev/null | grep -q automation-hub-waha; then
  ok "WAHA container running"
  if WAHA_API_KEY="${WAHA_API_KEY:-automation-hub-test-key}" "$HUB_HOME/run-task.sh" waha-status >/dev/null 2>&1; then
    ok "waha-status"
  else
    bad "waha-status (scan QR di http://localhost:3000)"
  fi
else
  bad "WAHA container (jalankan: bash install-all.sh)"
fi

# 6. Port 3000
if curl -sf --connect-timeout 2 http://localhost:3000/ >/dev/null 2>&1 || \
   curl -s --connect-timeout 2 -o /dev/null -w "%{http_code}" http://localhost:3000/ | grep -qE '200|401|302'; then
  ok "http://localhost:3000"
else
  bad "http://localhost:3000 unreachable"
fi

# 7. SSH key
[[ -f "$HOME/.ssh/automation_hub.pub" ]] && ok "SSH key automation_hub" || bad "SSH key (jalankan install-all.sh)"

echo ""
echo "=== Result: $PASS passed, $FAIL failed ==="
[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
