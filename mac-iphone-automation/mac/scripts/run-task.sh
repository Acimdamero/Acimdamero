#!/bin/bash
# Entry point utama — dipanggil dari iPhone (SSH) atau daemon hub.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

usage() {
  cat <<'EOF'
Automation Hub — run-task.sh

Usage:
  run-task.sh <command> [args...]

Commands:
  status              Status Mac (disk, uptime, battery jika laptop)
  backup [target]     Backup folder ke Google Drive
  open-app <name>     Buka aplikasi Mac
  quit-app <name>     Tutup aplikasi Mac
  sleep               Tidurkan Mac
  wake                Bangunkan layar Mac
  cursor-pull <dir>   Git pull di project Cursor
  cursor-build <dir>  npm run build (jika ada package.json)
  queue-process       Proses antrian dari Google Sheet
  pushcut <shortcut> [input]  Trigger iPhone via Pushcut (instant)
  iphone-dispatch <cmd> [args]  Kirim perintah ke iPhone (Pushcut/Sheet)
  whatsapp-send <phone> <msg>   Kirim WA (backend: meta|waha)
  waha-send <phone> <msg>       Kirim WA via WAHA self-hosted
  waha-send-name <name> [msg]   Cari kontak by name + kirim (WAHA)
  waha-status                   Cek session WAHA
  waha-auto-reply [start|stop]  Auto-reply pesan masuk (webhook lokal)
  edtime-open                   Buka edtime di iPhone (dispatch)
  edtime-fetch [week=current]   Fetch jadwal + SS dari iPhone
  edtime-sync full              Pipeline lengkap fetch→process→export
  edtime-process                Proses inbox Drive + merge Sheet
  edtime-export                 Export latest.json untuk Cursor
  edtime-status                 Status export edtime
  edtime-monitor [status|watch] Dashboard monitor (Anda)
  edtime-agent [run|sync|...]   Orchestrator agentic
  edtime-credentials            Simpan webhook/user edtime ke Keychain
  help                Tampilkan bantuan ini

Contoh:
  run-task.sh status
  run-task.sh backup documents
  run-task.sh open-app Safari
  run-task.sh cursor-pull ~/Developer/my-app
EOF
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  status)
    exec "$SCRIPT_DIR/status.sh" "$@"
    ;;
  backup)
    exec "$SCRIPT_DIR/backup.sh" "$@"
    ;;
  open-app|quit-app)
    exec "$SCRIPT_DIR/app-control.sh" "$cmd" "$@"
    ;;
  sleep)
    log "INFO" "Sleep requested"
    pmset sleepnow
    ;;
  wake)
    log "INFO" "Wake requested"
    caffeinate -u -t 2
    ;;
  cursor-pull|cursor-build)
    exec "$SCRIPT_DIR/cursor-workflow.sh" "$cmd" "$@"
    ;;
  queue-process)
    exec "$SCRIPT_DIR/queue-processor.sh" "$@"
    ;;
  pushcut)
    exec "$SCRIPT_DIR/pushcut-trigger.sh" "$@"
    ;;
  iphone-dispatch)
    exec "$SCRIPT_DIR/iphone-dispatch.sh" "$@"
    ;;
  whatsapp-send)
    exec "$SCRIPT_DIR/whatsapp-send.sh" "$@"
    ;;
  waha-send)
    exec "$SCRIPT_DIR/waha-send.sh" "$@"
    ;;
  waha-send-name)
    exec "$SCRIPT_DIR/waha-send-by-name.sh" "$@"
    ;;
  waha-status)
    exec "$SCRIPT_DIR/waha-status.sh" "$@"
    ;;
  waha-auto-reply)
    exec "$SCRIPT_DIR/waha-auto-reply.sh" "$@"
    ;;
  edtime-open)
    exec "$SCRIPT_DIR/edtime-sync.sh" open "$@"
    ;;
  edtime-fetch)
    exec "$SCRIPT_DIR/edtime-sync.sh" fetch "$@"
    ;;
  edtime-sync)
    exec "$SCRIPT_DIR/edtime-sync.sh" "$@"
    ;;
  edtime-process)
    exec "$SCRIPT_DIR/edtime-process.sh" run "$@"
    ;;
  edtime-export)
    exec "$SCRIPT_DIR/edtime-export-cursor.sh" "$@"
    ;;
  edtime-status)
    exec "$SCRIPT_DIR/edtime-sync.sh" status "$@"
    ;;
  edtime-credentials)
    exec "$SCRIPT_DIR/edtime-save-credentials.sh" "$@"
    ;;
  edtime-monitor)
    exec "$SCRIPT_DIR/edtime-monitor.sh" "$@"
    ;;
  edtime-agent)
    exec "$SCRIPT_DIR/edtime-agent-orchestrator.sh" "$@"
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    log "ERROR" "Unknown command: $cmd"
    usage
    exit 1
    ;;
esac
