#!/bin/bash
# Start WAHA + tampilkan QR — pakai docker-autostart jika ada.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
export AUTOMATION_REPO="$REPO_DIR"

if [[ -x "$HUB_HOME/scripts/docker-autostart.sh" ]]; then
  bash "$HUB_HOME/scripts/docker-autostart.sh"
else
  bash "$REPO_DIR/mac/scripts/docker-autostart.sh"
fi
