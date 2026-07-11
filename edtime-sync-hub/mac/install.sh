#!/bin/bash
# Installer edtime-sync-hub (standalone — tanpa WAHA/Mac hub)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYNC_HOME="${EDTIME_SYNC_HOME:-$HOME/.edtime-sync}"

echo "==> Edtime Sync Hub Installer"
echo "    Repo: $REPO_DIR"
echo "    Home: $SYNC_HOME"

mkdir -p "$SYNC_HOME"/{logs,edtime,scripts,bin,agent}

cp -R "$REPO_DIR/mac/scripts/"* "$SYNC_HOME/scripts/"
cp "$REPO_DIR/mac/agent/"* "$SYNC_HOME/agent/" 2>/dev/null || true
chmod +x "$SYNC_HOME/scripts/"*.sh "$SYNC_HOME/agent/"*.sh 2>/dev/null || true

rm -f "$SYNC_HOME/run-edtime.sh"
cat > "$SYNC_HOME/run-edtime.sh" <<'W'
#!/bin/bash
S="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$S/scripts/run-edtime.sh" "$@"
W
chmod +x "$SYNC_HOME/run-edtime.sh"
ln -sf "$SYNC_HOME/scripts/run-edtime.sh" "$SYNC_HOME/bin/run-edtime" 2>/dev/null || true

if [[ ! -f "$SYNC_HOME/config.env" ]]; then
  cp "$REPO_DIR/config/config.example.env" "$SYNC_HOME/config.env"
fi
if [[ ! -f "$SYNC_HOME/edtime-mapping.json" ]]; then
  cp "$REPO_DIR/config/edtime-mapping.json.example" "$SYNC_HOME/edtime-mapping.json"
fi

grep -q '^EDTIME_SYNC_HOME=' "$SYNC_HOME/config.env" 2>/dev/null || \
  echo "EDTIME_SYNC_HOME=$SYNC_HOME" >> "$SYNC_HOME/config.env"
grep -q '^EDTIME_REPO=' "$SYNC_HOME/config.env" 2>/dev/null || \
  echo "EDTIME_REPO=$REPO_DIR" >> "$SYNC_HOME/config.env"

if [[ "$(uname -s)" == "Darwin" ]] && command -v launchctl >/dev/null 2>&1; then
  PLIST="$HOME/Library/LaunchAgents/com.edtime.sync.plist"
  sed -e "s|__SYNC_HOME__|$SYNC_HOME|g" -e "s|__REPO_DIR__|$REPO_DIR|g" \
    "$REPO_DIR/mac/launchd/com.edtime.sync.plist.template" > "$PLIST"
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST" 2>/dev/null || true
  echo "    LaunchAgent com.edtime.sync loaded"
fi

echo ""
echo "==> Selesai. Test: $SYNC_HOME/run-edtime.sh status"
echo "    Secrets: bash $REPO_DIR/install-secrets.sh"
