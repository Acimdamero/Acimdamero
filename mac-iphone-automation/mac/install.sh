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

# Entry point wrapper (must not overwrite scripts/run-task.sh via symlink)
rm -f "$HUB_HOME/run-task.sh"
cat > "$HUB_HOME/run-task.sh" <<'WRAPPER'
#!/bin/bash
HUB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$HUB/scripts/run-task.sh" "$@"
WRAPPER
chmod +x "$HUB_HOME/run-task.sh"
ln -sf "$HUB_HOME/scripts/run-task.sh" "$HUB_HOME/bin/run-task"

# Config
if [[ ! -f "$HUB_HOME/config.env" ]]; then
  cp "$REPO_DIR/config/config.example.env" "$HUB_HOME/config.env"
  echo "    Config dibuat: $HUB_HOME/config.env (edit sebelum production)"
else
  # Patch legacy unquoted paths
  sed -i.bak \
    -e 's|^GOOGLE_DRIVE_BACKUP_FOLDER=Automation Hub/Backups|GOOGLE_DRIVE_BACKUP_FOLDER="Automation Hub/Backups"|' \
    -e 's|^GOOGLE_DRIVE_LOG_FOLDER=Automation Hub/Logs|GOOGLE_DRIVE_LOG_FOLDER="Automation Hub/Logs"|' \
    "$HUB_HOME/config.env" 2>/dev/null || true
fi

# LaunchAgent hub daemon (macOS only)
if [[ "$(uname -s)" == "Darwin" ]] && command -v launchctl >/dev/null 2>&1; then
  mkdir -p "$LAUNCH_AGENTS"
  sed "s|__HUB_HOME__|$HUB_HOME|g" "$REPO_DIR/mac/launchd/com.automation.hub.plist.template" \
    > "$LAUNCH_AGENTS/${PLIST_LABEL}.plist"
  launchctl unload "$LAUNCH_AGENTS/${PLIST_LABEL}.plist" 2>/dev/null || true
  launchctl load "$LAUNCH_AGENTS/${PLIST_LABEL}.plist"
  echo "    LaunchAgent hub daemon loaded"

  # Docker + WAHA autostart (optional, enabled by default)
  if [[ "${INSTALL_DOCKER_AUTOSTART:-1}" == "1" ]]; then
    sed -e "s|__HUB_HOME__|$HUB_HOME|g" -e "s|__REPO_DIR__|$REPO_DIR|g" \
      "$REPO_DIR/mac/launchd/com.automation.docker-waha.plist.template" \
      > "$LAUNCH_AGENTS/com.automation.docker-waha.plist"
    grep -q '^AUTOMATION_REPO=' "$HUB_HOME/config.env" 2>/dev/null && \
      sed -i.bak "s|^AUTOMATION_REPO=.*|AUTOMATION_REPO=$REPO_DIR|" "$HUB_HOME/config.env" || \
      echo "AUTOMATION_REPO=$REPO_DIR" >> "$HUB_HOME/config.env"
    launchctl unload "$LAUNCH_AGENTS/com.automation.docker-waha.plist" 2>/dev/null || true
    launchctl load "$LAUNCH_AGENTS/com.automation.docker-waha.plist"
    echo "    LaunchAgent docker-waha autostart loaded"
  fi
else
  echo "    LaunchAgent skipped (macOS only)"
fi

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
