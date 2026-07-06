#!/bin/bash
# Aktifkan Docker + WAHA autostart saat login Mac.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

[[ "$(uname -s)" != "Darwin" ]] && {
  echo "Script ini hanya untuk macOS"
  exit 1
}

echo "==> Enable Docker + WAHA autostart"

# Install hub scripts dulu
bash "$REPO_DIR/mac/install.sh"

# Simpan path repo di config
CONFIG="$HUB_HOME/config.env"
grep -q '^AUTOMATION_REPO=' "$CONFIG" 2>/dev/null && \
  sed -i.bak "s|^AUTOMATION_REPO=.*|AUTOMATION_REPO=$REPO_DIR|" "$CONFIG" || \
  echo "AUTOMATION_REPO=$REPO_DIR" >> "$CONFIG"
grep -q '^DOCKER_AUTOSTART=' "$CONFIG" 2>/dev/null || \
  echo "DOCKER_AUTOSTART=1" >> "$CONFIG"

# LaunchAgent docker-waha
sed -e "s|__HUB_HOME__|$HUB_HOME|g" -e "s|__REPO_DIR__|$REPO_DIR|g" \
  "$REPO_DIR/mac/launchd/com.automation.docker-waha.plist.template" \
  > "$LAUNCH_AGENTS/com.automation.docker-waha.plist"

launchctl unload "$LAUNCH_AGENTS/com.automation.docker-waha.plist" 2>/dev/null || true
launchctl load "$LAUNCH_AGENTS/com.automation.docker-waha.plist"

echo ""
echo "✅ Autostart aktif!"
echo ""
echo "Yang terjadi otomatis:"
echo "  • Saat login Mac → Docker Desktop dibuka otomatis"
echo "  • WAHA container start otomatis"
echo "  • Cek ulang setiap 1 jam"
echo ""
echo "Log: $HUB_HOME/logs/docker-autostart.log"
echo ""
echo "Opsional — di Docker Desktop:"
echo "  Settings → General → ✅ Start Docker Desktop when you log in"
echo ""
echo "Test sekarang:"
echo "  bash $HUB_HOME/scripts/docker-autostart.sh"
echo ""
echo "Matikan autostart:"
echo "  launchctl unload ~/Library/LaunchAgents/com.automation.docker-waha.plist"
echo "  echo 'DOCKER_AUTOSTART=0' >> $CONFIG"
