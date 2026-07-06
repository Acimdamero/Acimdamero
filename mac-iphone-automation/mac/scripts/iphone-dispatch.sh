#!/bin/bash
# Dispatch perintah ke iPhone — Pushcut (instant) atau fallback Google Sheet queue.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

COMMAND="${1:?Command required e.g. notify}"
ARGS="${2:-}"
MODE="${DISPATCH_MODE:-pushcut}"

INPUT="${COMMAND}"
if [[ -n "$ARGS" ]]; then
  INPUT="${COMMAND}|${ARGS}"
fi

case "$MODE" in
  pushcut)
    exec "$SCRIPT_DIR/pushcut-trigger.sh" "Hub — Execute Command" "$INPUT"
    ;;
  sheet)
    log "INFO" "Fallback Sheet queue: iphone/$COMMAND/$ARGS"
    WEBHOOK="$(get_keychain_secret "webhook-url" 2>/dev/null || true)"
    if [[ -z "$WEBHOOK" ]]; then
      log "ERROR" "webhook-url tidak ada di Keychain untuk fallback Sheet"
      exit 1
    fi
    curl -sf -X POST "$WEBHOOK" \
      -H "Content-Type: application/json" \
      -d "{\"device\":\"iphone\",\"command\":\"$COMMAND\",\"args\":\"$ARGS\"}"
    ;;
  both)
    "$SCRIPT_DIR/pushcut-trigger.sh" "Hub — Execute Command" "$INPUT" || true
    DISPATCH_MODE=sheet "$0" "$COMMAND" "$ARGS"
    ;;
  *)
    log "ERROR" "Unknown DISPATCH_MODE: $MODE (pushcut|sheet|both)"
    exit 1
    ;;
esac
