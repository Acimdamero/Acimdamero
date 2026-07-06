#!/bin/bash
# Trigger Pushcut Automation Server — eksekusi Shortcut iPhone instantly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

SHORTCUT_NAME="${1:?Shortcut name required}"
INPUT="${2:-}"
TIMEOUT="${PUSHCUT_TIMEOUT:-nowait}"

SECRET="${PUSHCUT_SECRET:-}"
if [[ -z "$SECRET" ]]; then
  SECRET="$(get_keychain_secret "pushcut-secret" 2>/dev/null || true)"
fi
if [[ -z "$SECRET" ]]; then
  SECRET="$(get_op_secret "Pushcut" "credential" 2>/dev/null || true)"
fi
if [[ -z "$SECRET" ]]; then
  log "ERROR" "PUSHCUT_SECRET tidak ditemukan. Set env atau Keychain pushcut-secret"
  exit 1
fi

ENCODED_NAME=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$SHORTCUT_NAME")
URL="https://api.pushcut.io/${SECRET}/execute?shortcut=${ENCODED_NAME}&timeout=${TIMEOUT}"

if [[ -n "$INPUT" ]]; then
  ENCODED_INPUT=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$INPUT")
  URL="${URL}&input=${ENCODED_INPUT}"
fi

log "INFO" "Pushcut trigger: $SHORTCUT_NAME"
RESPONSE=$(curl -sf -X POST "$URL" || curl -sf "$URL")
log "INFO" "Pushcut response: $RESPONSE"
echo "$RESPONSE"
