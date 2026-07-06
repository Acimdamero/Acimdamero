#!/bin/bash
# Kirim WhatsApp via WAHA (WhatsApp HTTP API) — self-hosted, personal account.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

TO="${1:?Phone E.164 digits e.g. 6281234567890}"
MESSAGE="${2:?Message text required}"

BASE_URL="${WAHA_BASE_URL:-http://localhost:3000}"
SESSION="${WAHA_SESSION:-default}"
API_KEY="${WAHA_API_KEY:-}"

if [[ -z "$API_KEY" ]]; then
  API_KEY="$(get_keychain_secret "waha-api-key" 2>/dev/null || true)"
fi

TO=$(echo "$TO" | tr -cd '0-9')
CHAT_ID="${TO}@c.us"

PAYLOAD=$(python3 - "$SESSION" "$CHAT_ID" "$MESSAGE" <<'PY'
import json, sys
session, chat_id, text = sys.argv[1], sys.argv[2], sys.argv[3]
print(json.dumps({"session": session, "chatId": chat_id, "text": text}))
PY
)

HEADERS=(-H "Content-Type: application/json")
if [[ -n "$API_KEY" ]]; then
  HEADERS+=(-H "X-Api-Key: ${API_KEY}")
fi

log "INFO" "WAHA send to $CHAT_ID via $BASE_URL"
RESPONSE=$(curl -sf -X POST "${BASE_URL}/api/sendText" "${HEADERS[@]}" -d "$PAYLOAD")
log "INFO" "WAHA OK"
echo "$RESPONSE"

WEBHOOK="$(get_keychain_secret "webhook-url" 2>/dev/null || true)"
if [[ -n "$WEBHOOK" ]]; then
  curl -sf -X POST "$WEBHOOK" \
    -H "Content-Type: application/json" \
    -d "{\"action\":\"wa_sent\",\"backend\":\"waha\",\"to\":\"$TO\",\"message\":\"$MESSAGE\"}" >/dev/null 2>&1 || true
fi
