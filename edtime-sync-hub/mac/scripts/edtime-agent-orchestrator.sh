#!/bin/bash
# Agentic orchestrator edtime — install, sync, export, laporkan status.
# Dipanggil oleh run-agent.sh dan LaunchAgent edtime.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SYNC_HOME="${EDTIME_SYNC_HOME:-$HOME/.edtime-sync}"
HUB_HOME="$SYNC_HOME"
# shellcheck source=edtime-lib.sh
source "$SCRIPT_DIR/edtime-lib.sh"

load_secrets() {
  local f
  for f in "$SYNC_HOME/secrets.env" "$REPO_DIR/config/secrets.env" "$REPO_DIR/config/secrets.ready.env"; do
    if [[ -f "$f" ]]; then
      set -a
      # shellcheck disable=SC1090
      source "$f"
      set +a
      edtime_log "INFO" "Loaded secrets from $f"
      return 0
    fi
  done
  return 0
}

write_report() {
  local phase="$1" status="$2" message="$3"
  local report_dir report_file
  report_dir="$(edtime_resolve_drive_base "$EDTIME_DRIVE_FOLDER/cursor")"
  mkdir -p "$report_dir" "$HUB_HOME/edtime"
  report_file="$HUB_HOME/edtime/agent-report.json"
  python3 - "$phase" "$status" "$message" "$report_file" <<'PY'
import json, sys
from datetime import datetime, timezone
phase, status, msg, path = sys.argv[1:5]
try:
    with open(path) as f:
        r = json.load(f)
except Exception:
    r = {"history": []}
r.update({
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "phase": phase,
    "status": status,
    "message": msg,
})
r.setdefault("history", []).append({
    "at": r["updated_at"], "phase": phase, "status": status, "message": msg
})
r["history"] = r["history"][-50:]
with open(path, "w") as f:
    json.dump(r, f, indent=2, ensure_ascii=False)
print(path)
PY
  cp "$report_file" "$report_dir/agent-report.json" 2>/dev/null || true
}

check_webhook_setup() {
  local url
  url="$(edtime_webhook_url 2>/dev/null || true)"
  [[ -n "$url" ]] || return 1
  curl -sf "${url%%\?*}?action=setup-edtime" >/dev/null 2>&1 && return 0
  curl -sf "$url" >/dev/null 2>&1
}

phase_install() {
  write_report "install" "running" "Installing edtime-sync-hub scripts"
  bash "$REPO_DIR/mac/install.sh"
  bash "$REPO_DIR/setup-edtime-sync.sh" --non-interactive
  write_report "install" "ok" "edtime-sync-hub installed"
}

phase_configure() {
  write_report "configure" "running" "Applying secrets.env"
  local CONFIG="$HUB_HOME/config.env"
  touch "$CONFIG"
  if [[ -n "${GOOGLE_SHEET_ID:-}" ]]; then
    grep -q '^GOOGLE_SHEET_ID=' "$CONFIG" && \
      sed -i.bak "s|^GOOGLE_SHEET_ID=.*|GOOGLE_SHEET_ID=$GOOGLE_SHEET_ID|" "$CONFIG" || \
      echo "GOOGLE_SHEET_ID=$GOOGLE_SHEET_ID" >> "$CONFIG"
  fi
  if [[ -n "${HUB_WEBHOOK_URL:-}" ]]; then
    "$SCRIPT_DIR/edtime-save-credentials.sh" webhook "$HUB_WEBHOOK_URL"
  fi
  if [[ -n "${EDTIME_USER:-}" ]]; then
    "$SCRIPT_DIR/edtime-save-credentials.sh" edtime-user "$EDTIME_USER"
  fi
  check_webhook_setup && write_report "configure" "ok" "Webhook reachable" || \
    write_report "configure" "warn" "Webhook belum OK — deploy Apps Script + isi HUB_WEBHOOK_URL"
}

phase_enable_autostart() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    write_report "autostart" "skip" "LaunchAgent macOS only"
    return 0
  fi
  write_report "autostart" "running" "Loading LaunchAgent com.edtime.sync"
  local LA="$HOME/Library/LaunchAgents"
  mkdir -p "$LA"
  sed -e "s|__SYNC_HOME__|$HUB_HOME|g" -e "s|__REPO_DIR__|$REPO_DIR|g" \
    "$REPO_DIR/mac/launchd/com.edtime.sync.plist.template" \
    > "$LA/com.edtime.sync.plist"
  launchctl unload "$LA/com.edtime.sync.plist" 2>/dev/null || true
  launchctl load "$LA/com.edtime.sync.plist" 2>/dev/null || true
  write_report "autostart" "ok" "Daemon edtime sync scheduled"
}

phase_sync_pipeline() {
  if [[ "${SKIP_IPHONE_DISPATCH:-0}" == "1" ]]; then
    write_report "sync" "skip" "SKIP_IPHONE_DISPATCH=1"
    "$SCRIPT_DIR/edtime-process.sh" run
    "$SCRIPT_DIR/edtime-export-cursor.sh"
    return 0
  fi
  write_report "sync" "running" "Dispatch edtime-fetch ke iPhone"
  "$SCRIPT_DIR/edtime-sync.sh" fetch week=current || true
  local timeout="${EDTIME_FETCH_TIMEOUT:-900}"
  local elapsed=0 interval=30
  while [[ "$elapsed" -lt "$timeout" ]]; do
    if ! "$SCRIPT_DIR/edtime-process.sh" check-pending; then
      break
    fi
    sleep "$interval"
    elapsed=$((elapsed + interval))
    edtime_log "INFO" "Waiting iPhone fetch... ${elapsed}s"
  done
  "$SCRIPT_DIR/edtime-process.sh" run
  "$SCRIPT_DIR/edtime-export-cursor.sh"
  write_report "sync" "ok" "Pipeline complete — cek latest.json"
}

phase_notify() {
  if [[ "${EDTIME_NOTIFY_ON_COMPLETE:-1}" != "1" ]]; then
    return 0
  fi
  "$SCRIPT_DIR/iphone-dispatch.sh" notify "edtime agent selesai — buka Cursor latest.json" 2>/dev/null || true
}

write_pending_decisions() {
  local f="$HUB_HOME/edtime/pending-decisions.json"
  python3 - "$f" <<'PY'
import json, os, sys
from datetime import datetime, timezone

hub = os.path.expanduser("~/.edtime-sync")
decisions = []

def need(cond, id_, title, action, priority="high"):
    if cond:
        decisions.append({
            "id": id_, "title": title, "action": action,
            "priority": priority, "status": "pending",
        })

webhook = os.popen(
    "security find-generic-password -s edtime-sync -a webhook-url -w 2>/dev/null"
).read().strip()
need(not webhook, "deploy_apps_script",
     "Deploy Apps Script + isi HUB_WEBHOOK_URL di secrets.env",
     "Extensions→Apps Script→Deploy Web App→bash run-agent.sh")

sheet = ""
cfg = os.path.join(hub, "config.env")
if os.path.isfile(cfg):
    for line in open(cfg):
        if line.startswith("GOOGLE_SHEET_ID="):
            sheet = line.split("=", 1)[1].strip()
need(not sheet or sheet == "your_google_sheet_id_here", "google_sheet_id",
     "Isi GOOGLE_SHEET_ID di secrets.env",
     "Copy dari URL Google Sheet")

need(True, "iphone_shortcuts",
     "Buat Shortcut Hub — edtime Fetch di iPhone (sekali)",
     "iphone/EDTIME-SHORTCUTS-SETUP.md", "medium")

need(True, "edtime_login_once",
     "Login edtime app di iPhone + SS Schichtplan saat fetch",
     "Buka edtime → login → jalankan fetch dari Mac", "medium")

out = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "decisions": decisions,
    "monitor_command": "~/.edtime-sync/scripts/edtime-monitor.sh",
}
with open(sys.argv[1], "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(sys.argv[1])
PY
}

run_all_phases() {
  load_secrets
  load_config
  edtime_ensure_folders
  write_pending_decisions

  phase_install
  phase_configure
  phase_enable_autostart

  if [[ "${EDTIME_RUN_SYNC:-1}" == "1" ]]; then
    phase_sync_pipeline
    phase_notify
  fi

  write_report "complete" "ok" "Agentic setup finished — monitor: edtime-monitor.sh"
  "$SCRIPT_DIR/edtime-monitor.sh" || true
}

cmd="${1:-run}"
case "$cmd" in
  run) run_all_phases ;;
  install) load_secrets; phase_install ;;
  configure) load_secrets; load_config; phase_configure ;;
  sync) load_secrets; load_config; phase_sync_pipeline; phase_notify ;;
  pending) write_pending_decisions; cat "$HUB_HOME/edtime/pending-decisions.json" ;;
  *)
    echo "Usage: edtime-agent-orchestrator.sh [run|install|configure|sync|pending]"
    exit 1
    ;;
esac
