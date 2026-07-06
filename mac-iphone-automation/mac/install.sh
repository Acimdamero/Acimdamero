#!/bin/bash
# Installer Automation Hub di Mac.
# Usage: bash install.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST_LABEL="com.automation.hub"

echo "==> Automation Hub Installer"
echo "    Repo: $REPO_DIR"
echo "    Hub:  $HUB_HOME"

mkdir -p "$HUB_HOME"/{logs,backups,scripts,agent,bin}

# Copy scripts & agent
cp -R "$REPO_DIR/mac/scripts/"* "$HUB_HOME/scripts/"
cp -R "$REPO_DIR/mac/agent/"* "$HUB_HOME/agent/"
chmod +x "$HUB_HOME/scripts/"*.sh "$HUB_HOME/agent/"*.sh

# Symlink run-task ke bin
ln -sf "$HUB_HOME/scripts/run-task.sh" "$HUB_HOME/bin/run-task"
ln -sf "$HUB_HOME/scripts/run-task.sh" "$HUB_HOME/run-task.sh"

# Config
if [[ ! -f "$HUB_HOME/config.env" ]]; then
  cp "$REPO_DIR/config/config.example.env" "$HUB_HOME/config.env"
  echo "    Config dibuat: $HUB_HOME/config.env (edit sebelum production)"
fi

# LaunchAgent
mkdir -p "$LAUNCH_AGENTS"
sed "s|__HUB_HOME__|$HUB_HOME|g" "$REPO_DIR/mac/launchd/com.automation.hub.plist.template" \
  > "$LAUNCH_AGENTS/${PLIST_LABEL}.plist"

launchctl unload "$LAUNCH_AGENTS/${PLIST_LABEL}.plist" 2>/dev/null || true
launchctl load "$LAUNCH_AGENTS/${PLIST_LABEL}.plist"

echo ""
echo "==> Instalasi selesai!"
echo ""
echo "Langkah berikutnya:"
echo "  1. Edit $HUB_HOME/config.env (Google Sheet ID, backup paths)"
echo "  2. System Settings > Sharing > Remote Login ON"
echo "  3. Test: $HUB_HOME/run-task.sh status"
echo "  4. iPhone Shortcuts: lihat iphone/SHORTCUTS-GUIDE.md"
echo ""
echo "SSH dari iPhone:"
echo "  $HUB_HOME/run-task.sh backup all"
