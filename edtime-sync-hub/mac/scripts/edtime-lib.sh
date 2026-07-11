#!/bin/bash
# Library edtime — dipakai oleh edtime-sync.sh, edtime-process.sh, edtime-export-cursor.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

HUB_HOME="${EDTIME_SYNC_HOME:-$HOME/.edtime-sync}"
SYNC_HOME="$HUB_HOME"
EDTIME_MAPPING="${EDTIME_MAPPING:-$SYNC_HOME/edtime-mapping.json}"
EDTIME_DRIVE_FOLDER="${EDTIME_DRIVE_FOLDER:-Edtime Sync}"
EDTIME_CURSOR_JSON="${EDTIME_CURSOR_JSON:-cursor/latest.json}"

edtime_log() {
  log "EDTIME" "$@"
}

edtime_resolve_drive_base() {
  local sub="${1:-}"
  local base
  base="$(resolve_drive_base)"
  if [[ -n "$sub" ]]; then
    echo "${base}/${sub}"
  else
    echo "$base"
  fi
}

edtime_ensure_folders() {
  local dirs=(
    "$(edtime_resolve_drive_base "$EDTIME_DRIVE_FOLDER")"
    "$(edtime_resolve_drive_base "$EDTIME_DRIVE_FOLDER/Screenshots")"
    "$(edtime_resolve_drive_base "$EDTIME_DRIVE_FOLDER/inbox")"
    "$(edtime_resolve_drive_base "$EDTIME_DRIVE_FOLDER/cursor")"
    "$HUB_HOME/edtime"
  )
  local d
  for d in "${dirs[@]}"; do
    mkdir -p "$d"
  done
}

edtime_webhook_url() {
  local url
  url="$(get_keychain_secret "webhook-url" 2>/dev/null || true)"
  if [[ -z "$url" ]]; then
    url="${EDTIME_WEBHOOK_URL:-${HUB_WEBHOOK_URL:-}}"
  fi
  if [[ -z "$url" ]]; then
    edtime_log "ERROR" "Webhook URL belum diset. Jalankan: setup-edtime-sync.sh"
    return 1
  fi
  echo "$url"
}

edtime_post_json() {
  local payload="$1"
  local url
  url="$(edtime_webhook_url)"
  curl -sf -X POST "$url" \
    -H "Content-Type: application/json" \
    -d "$payload"
}

edtime_get_export() {
  local url action="${1:-cursor-edtime-export}"
  url="$(edtime_webhook_url)"
  # Strip trailing slash, append query
  url="${url%/}"
  if [[ "$url" == *"?"* ]]; then
    curl -sf "${url}&action=${action}"
  else
    curl -sf "${url}?action=${action}"
  fi
}

edtime_hours_between() {
  python3 - "$1" "$2" "$3" <<'PY'
import sys
from datetime import datetime

def parse(t):
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(t.strip(), fmt)
        except ValueError:
            pass
    return None

start, end, br = sys.argv[1], sys.argv[2], sys.argv[3]
s, e = parse(start), parse(end)
if not s or not e:
    print("0")
    sys.exit(0)
if e < s:
    from datetime import timedelta
    e = e + timedelta(days=1)
break_m = float(br or 0)
hours = (e - s).total_seconds() / 3600.0 - break_m / 60.0
print(f"{max(0, hours):.2f}")
PY
}
