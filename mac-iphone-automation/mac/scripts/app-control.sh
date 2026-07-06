#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

ACTION="${1:?Action required: open-app or quit-app}"
APP_NAME="${2:?App name required}"

case "$ACTION" in
  open-app)
    log "INFO" "Opening app: $APP_NAME"
    open -a "$APP_NAME"
    ;;
  quit-app)
    log "INFO" "Quitting app: $APP_NAME"
    osascript -e "tell application \"$APP_NAME\" to quit" 2>/dev/null || killall "$APP_NAME" 2>/dev/null || {
      log "ERROR" "Gagal menutup: $APP_NAME"
      exit 1
    }
    ;;
  *)
    log "ERROR" "Unknown action: $ACTION"
    exit 1
    ;;
esac

echo "{\"status\":\"done\",\"action\":\"$ACTION\",\"app\":\"$APP_NAME\"}"
