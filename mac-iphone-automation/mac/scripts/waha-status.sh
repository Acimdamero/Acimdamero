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
if RESPONSE=$(curl -sf "${HEADERS[@]}" "$URL" 2>/dev/null); then
  log "INFO" "WAHA session $SESSION reachable"
  echo "$RESPONSE"
else
  log "ERROR" "WAHA tidak reachable di $BASE_URL — jalankan: docker compose -f docker/docker-compose.waha.yml up -d"
  exit 1
fi
