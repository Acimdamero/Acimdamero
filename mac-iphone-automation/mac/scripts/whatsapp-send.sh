#!/bin/bash
# Kirim WhatsApp via Meta Cloud API (Business) — full auto, tanpa tap Send.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

TO="${1:?Recipient phone E.164 digits e.g. 6281234567890}"
MESSAGE="${2:?Message text required}"

TOKEN="${WHATSAPP_ACCESS_TOKEN:-}"
PHONE_ID="${WHATSAPP_PHONE_NUMBER_ID:-}"

if [[ -z "$TOKEN" ]]; then
  TOKEN="$(get_keychain_secret "wa-token" 2>/dev/null || true)"
fi
if [[ -z "$PHONE_ID" ]]; then
  PHONE_ID="$(get_keychain_secret "wa-phone-id" 2>/dev/null || true)"
fi
if [[ -z "$TOKEN" || -z "$PHONE_ID" ]]; then
  log "ERROR" "WhatsApp Business API belum dikonfigurasi."
  log "ERROR" "Set WHATSAPP_ACCESS_TOKEN + WHATSAPP_PHONE_NUMBER_ID atau Keychain wa-token / wa-phone-id"
  exit 1
fi

# Normalize phone: digits only
TO=$(echo "$TO" | tr -cd '0-9')

API_URL="https://graph.facebook.com/v21.0/${PHONE_ID}/messages"

PAYLOAD=$(python3 - "$TO" "$MESSAGE" <<'PY'
import json, sys
to, text = sys.argv[1], sys.argv[2]
print(json.dumps({
  "messaging_product": "whatsapp",
  "to": to,
  "type": "text",
  "text": {"body": text}
}))
PY
)

log "INFO" "WhatsApp send to $TO"
RESPONSE=$(curl -sf -X POST "$API_URL" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

log "INFO" "WhatsApp API OK"
echo "$RESPONSE"

# Log ke Sheet via webhook opsional
WEBHOOK="$(get_keychain_secret "webhook-url" 2>/dev/null || true)"
if [[ -n "$WEBHOOK" ]]; then
  curl -sf -X POST "$WEBHOOK" \
    -H "Content-Type: application/json" \
    -d "{\"action\":\"wa_sent\",\"to\":\"$TO\",\"message\":\"$MESSAGE\"}" >/dev/null 2>&1 || true
fi
