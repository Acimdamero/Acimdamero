#!/bin/bash
# Cek status session WAHA.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

BASE_URL="${WAHA_BASE_URL:-http://localhost:3000}"
SESSION="${WAHA_SESSION:-default}"
API_KEY="${WAHA_API_KEY:-}"

if [[ -z "$API_KEY" ]]; then
  API_KEY="$(get_keychain_secret "waha-api-key" 2>/dev/null || true)"
fi

HEADERS=()
if [[ -n "$API_KEY" ]]; then
  HEADERS+=(-H "X-Api-Key: ${API_KEY}")
fi

URL="${BASE_URL}/api/sessions/${SESSION}"
HTTP_CODE=$(curl -s -o /tmp/waha-status.json -w "%{http_code}" "${HEADERS[@]}" "$URL" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
  log "INFO" "WAHA session $SESSION: WORKING"
  cat /tmp/waha-status.json
elif [[ "$HTTP_CODE" == "404" ]]; then
  log "WARN" "WAHA running — session belum ada. Scan QR di http://localhost:3000"
  echo '{"status":"needs_qr","session":"'"$SESSION"'","dashboard":"'"$BASE_URL"'"}'
elif [[ "$HTTP_CODE" == "401" ]]; then
  log "ERROR" "WAHA API key salah — set WAHA_API_KEY di config.env"
  exit 1
else
  log "ERROR" "WAHA tidak reachable di $BASE_URL (HTTP $HTTP_CODE)"
  exit 1
fi
