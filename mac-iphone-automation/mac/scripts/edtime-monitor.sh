#!/bin/bash
# Dashboard monitor — untuk Anda: lihat status, keputusan pending, test cepat.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
# shellcheck source=edtime-lib.sh
source "$SCRIPT_DIR/edtime-lib.sh"

load_config
edtime_ensure_folders

REPORT="$HUB_HOME/edtime/agent-report.json"
PENDING="$HUB_HOME/edtime/pending-decisions.json"
EXPORT_LOCAL="$HUB_HOME/edtime/cursor-latest.json"

print_header() {
  echo ""
  echo "╔══════════════════════════════════════════════════════════╗"
  echo "║  edtime AGENT — Monitor Dashboard                        ║"
  echo "╚══════════════════════════════════════════════════════════╝"
  echo ""
}

print_report() {
  echo "── Agent Report ──"
  if [[ -f "$REPORT" ]]; then
    python3 - "$REPORT" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    r = json.load(f)
print(f"  Status:   {r.get('status', '?')}")
print(f"  Phase:    {r.get('phase', '?')}")
print(f"  Message:  {r.get('message', '?')}")
print(f"  Updated:  {r.get('updated_at', '?')}")
PY
  else
    echo "  (belum ada — jalankan: bash run-edtime-agentic.sh)"
  fi
}

print_pending() {
  echo ""
  echo "── Keputusan / Aksi Anda ──"
  if [[ -f "$PENDING" ]]; then
    python3 - "$PENDING" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
for i, x in enumerate(d.get("decisions", []), 1):
    pri = x.get("priority", "")
    print(f"  [{pri}] {x.get('title', '?')}")
    print(f"         → {x.get('action', '')}")
    print()
PY
  else
    "$SCRIPT_DIR/edtime-agent-orchestrator.sh" pending 2>/dev/null || true
    [[ -f "$PENDING" ]] && print_pending || echo "  (generate: edtime-agent-orchestrator.sh pending)"
  fi
}

print_export() {
  echo "── Cursor Export ──"
  if [[ -f "$EXPORT_LOCAL" ]]; then
    python3 - "$EXPORT_LOCAL" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
print(f"  Records:  {len(d.get('schedule', []))}")
print(f"  Exported: {d.get('exported_at', '?')}")
print(f"  Path:     {sys.argv[1]}")
PY
  else
    echo "  (belum ada — tunggu sync selesai atau: run-task.sh edtime-export)"
  fi
}

print_webhook() {
  echo ""
  echo "── Webhook ──"
  if url="$(get_keychain_secret webhook-url 2>/dev/null)"; then
    echo "  ✅ Keychain: ${url:0:50}..."
    code=$(curl -s -o /dev/null -w "%{http_code}" "${url%%\?*}?action=cursor-edtime-export" 2>/dev/null || echo "000")
    echo "  HTTP cursor-edtime-export: $code"
  else
    echo "  ❌ webhook-url belum di Keychain"
  fi
}

print_daemon() {
  echo ""
  echo "── Daemons (macOS) ──"
  if [[ "$(uname -s)" == "Darwin" ]]; then
    launchctl list 2>/dev/null | grep -E 'com.automation.(hub|edtime)' || echo "  (LaunchAgent belum loaded)"
  else
    echo "  (hanya macOS)"
  fi
}

cmd="${1:-status}"
print_header
case "$cmd" in
  status)
    print_report
    print_webhook
    print_export
    print_pending
    print_daemon
    ;;
  watch)
    while true; do
      clear 2>/dev/null || true
      print_header
      print_report
      print_export
      print_pending
      echo "Refresh 30s — Ctrl+C stop"
      sleep 30
    done
    ;;
  test)
    echo "── Quick test ──"
    "$HUB_HOME/run-task.sh" edtime-status 2>/dev/null || "$SCRIPT_DIR/edtime-sync.sh" status
    ;;
  *)
    echo "Usage: edtime-monitor.sh [status|watch|test]"
    exit 1
    ;;
esac
echo ""
