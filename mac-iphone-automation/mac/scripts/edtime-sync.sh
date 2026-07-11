#!/bin/bash
# Orkestrator sinkronisasi edtime: dispatch iPhone fetch → proses → export Cursor.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=edtime-lib.sh
source "$SCRIPT_DIR/edtime-lib.sh"

usage() {
  cat <<'EOF'
edtime-sync.sh — pipeline sinkron edtime iPhone → Sheet → Cursor

Usage:
  edtime-sync.sh full [week=current]     Dispatch fetch + tunggu + process + export
  edtime-sync.sh fetch [week=current]    Kirim perintah edtime-fetch ke iPhone
  edtime-sync.sh process                 Proses inbox Drive + data Sheet
  edtime-sync.sh export                  Export JSON untuk Cursor (Drive + log)
  edtime-sync.sh session-log <status>    Log status session (logged_in|needs_login|error)
  edtime-sync.sh open                    Buka edtime di iPhone (dispatch)
  edtime-sync.sh status                  Ringkasan file export + tab Sheet

Contoh:
  edtime-sync.sh full week=current
  edtime-sync.sh fetch week=KW28
  edtime-sync.sh session-log needs_login
EOF
}

wait_for_iphone_fetch() {
  local timeout="${EDTIME_FETCH_TIMEOUT:-900}"
  local interval="${EDTIME_FETCH_POLL:-30}"
  local elapsed=0
  edtime_log "INFO" "Menunggu iPhone selesai fetch (max ${timeout}s, poll ${interval}s)..."
  while [[ "$elapsed" -lt "$timeout" ]]; do
    if "$SCRIPT_DIR/edtime-process.sh" check-pending; then
      sleep "$interval"
      elapsed=$((elapsed + interval))
    else
      edtime_log "INFO" "Fetch iPhone selesai atau tidak ada pending"
      return 0
    fi
  done
  edtime_log "WARN" "Timeout menunggu iPhone — lanjut proses data yang ada"
  return 0
}

cmd="${1:-help}"
shift || true

edtime_ensure_folders

PENDING_FLAG="$HUB_HOME/edtime/fetch-pending"

case "$cmd" in
  edtime-fetch)
    ARGS="${*:-week=current}"
    edtime_log "INFO" "Dispatch edtime-fetch ke iPhone: $ARGS"
    mkdir -p "$HUB_HOME/edtime"
    date -u +%Y-%m-%dT%H:%M:%SZ > "$PENDING_FLAG"
    exec "$SCRIPT_DIR/iphone-dispatch.sh" "edtime-fetch" "$ARGS"
    ;;
  open)
    exec "$SCRIPT_DIR/iphone-dispatch.sh" "edtime-open" ""
    ;;
  process)
    exec "$SCRIPT_DIR/edtime-process.sh" run "$@"
    ;;
  export)
    exec "$SCRIPT_DIR/edtime-export-cursor.sh" "$@"
    ;;
  session-log)
    STATUS="${1:-unknown}"
    edtime_post_json "{\"action\":\"edtime_session\",\"status\":\"$STATUS\",\"device\":\"mac\",\"at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
      && edtime_log "INFO" "Session log: $STATUS" || edtime_log "WARN" "Gagal POST session log"
    ;;
  status)
    EXPORT_DIR="$(edtime_resolve_drive_base "$EDTIME_DRIVE_FOLDER/cursor")"
    JSON_FILE="$EXPORT_DIR/latest.json"
    echo "=== edtime sync status ==="
    echo "Drive cursor export: $JSON_FILE"
    if [[ -f "$JSON_FILE" ]]; then
      echo "  size: $(wc -c < "$JSON_FILE") bytes"
      echo "  modified: $(stat -f '%Sm' "$JSON_FILE" 2>/dev/null || stat -c '%y' "$JSON_FILE" 2>/dev/null || echo '?')"
      python3 - "$JSON_FILE" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
print(f"  records: {len(d.get('schedule', []))}")
print(f"  exported_at: {d.get('exported_at', '?')}")
PY
    else
      echo "  (belum ada export — jalankan edtime-sync export)"
    fi
    ;;
  full)
    WEEK_ARGS="${*:-week=current}"
    edtime_log "INFO" "=== Pipeline edtime full: $WEEK_ARGS ==="
    "$SCRIPT_DIR/iphone-dispatch.sh" "edtime-fetch" "$WEEK_ARGS" || true
    wait_for_iphone_fetch
    "$SCRIPT_DIR/edtime-process.sh" run
    "$SCRIPT_DIR/edtime-export-cursor.sh"
    if [[ "${EDTIME_NOTIFY_ON_COMPLETE:-1}" == "1" ]]; then
      "$SCRIPT_DIR/iphone-dispatch.sh" "notify" "edtime sync selesai — data siap di Cursor" || true
    fi
    edtime_log "INFO" "=== Pipeline selesai ==="
    "$0" status
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    edtime_log "ERROR" "Perintah tidak dikenal: $cmd"
    usage
    exit 1
    ;;
esac
