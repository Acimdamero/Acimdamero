#!/bin/bash
# Entry point edtime-sync-hub

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

usage() {
  cat <<'EOF'
Edtime Sync Hub — run-edtime.sh

Usage:
  run-edtime.sh <command> [args...]

Commands:
  sync full [week=current]   Pipeline lengkap fetch→process→export
  fetch [week=current]       Dispatch edtime-fetch ke iPhone
  open                       Buka edtime di iPhone (Pushcut/Sheet)
  process                    Proses inbox + merge Sheet
  export                     Export latest.json untuk Cursor
  status                     Ringkasan export
  monitor [status|watch]     Dashboard monitor
  agent [run|sync|pending]   Orchestrator agentic
  credentials webhook <url>  Simpan webhook Keychain
  help

EOF
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  sync)    exec "$SCRIPT_DIR/edtime-sync.sh" full "$@" ;;
  fetch)   exec "$SCRIPT_DIR/edtime-sync.sh" fetch "$@" ;;
  open)    exec "$SCRIPT_DIR/edtime-sync.sh" open "$@" ;;
  process) exec "$SCRIPT_DIR/edtime-process.sh" run "$@" ;;
  export)  exec "$SCRIPT_DIR/edtime-export-cursor.sh" "$@" ;;
  status)  exec "$SCRIPT_DIR/edtime-sync.sh" status "$@" ;;
  monitor) exec "$SCRIPT_DIR/edtime-monitor.sh" "$@" ;;
  agent)   exec "$SCRIPT_DIR/edtime-agent-orchestrator.sh" "$@" ;;
  credentials) exec "$SCRIPT_DIR/edtime-save-credentials.sh" "$@" ;;
  help|-h|--help) usage ;;
  *)
    log "ERROR" "Unknown: $cmd"
    usage
    exit 1
    ;;
esac
