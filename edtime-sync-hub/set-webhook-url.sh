#!/bin/bash
# Set HUB_WEBHOOK_URL setelah deploy Apps Script.
# Usage: bash set-webhook-url.sh 'https://script.google.com/macros/s/.../exec'

set -euo pipefail

URL="${1:?Usage: bash set-webhook-url.sh 'WEB_APP_URL'}"
HUB_HOME="${EDTIME_SYNC_HOME:-$HOME/.edtime-sync}"
DEST="$HUB_HOME/secrets.env"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HUB_HOME"
[[ -f "$DEST" ]] || cp "$REPO_DIR/config/secrets.ready.env" "$DEST"

if grep -q '^HUB_WEBHOOK_URL=' "$DEST"; then
  sed -i.bak "s|^HUB_WEBHOOK_URL=.*|HUB_WEBHOOK_URL=$URL|" "$DEST"
else
  echo "HUB_WEBHOOK_URL=$URL" >> "$DEST"
fi

chmod 600 "$DEST"

# Keychain Mac
if [[ -x "$HUB_HOME/scripts/edtime-save-credentials.sh" ]]; then
  bash "$HUB_HOME/scripts/edtime-save-credentials.sh" webhook "$URL" 2>/dev/null || true
elif [[ -x "$REPO_DIR/mac/scripts/edtime-save-credentials.sh" ]]; then
  bash "$REPO_DIR/mac/scripts/edtime-save-credentials.sh" webhook "$URL"
fi

echo "✓ HUB_WEBHOOK_URL disimpan"
echo "  $DEST"
echo ""
echo "Test:"
echo "  curl \"${URL}?device=iphone\""
echo ""
echo "Lalu:"
echo "  bash $REPO_DIR/run-agent.sh"
