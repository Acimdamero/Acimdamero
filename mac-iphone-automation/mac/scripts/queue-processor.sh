#!/bin/bash
# Proses antrian perintah Mac dari Google Sheet via Sheets API.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

SHEET_ID="${GOOGLE_SHEET_ID:-}"
SHEET_RANGE="${GOOGLE_SHEET_RANGE:-Queue!A2:E100}"
RUN_TASK="${RUN_TASK:-$SCRIPT_DIR/run-task.sh}"

if [[ -z "$SHEET_ID" || "$SHEET_ID" == "your_google_sheet_id_here" ]]; then
  log "WARN" "GOOGLE_SHEET_ID belum diset — lewati queue-process."
  exit 0
fi

TOKEN="${GOOGLE_ACCESS_TOKEN:-}"
if [[ -z "$TOKEN" ]]; then
  TOKEN="$(get_op_secret "Google Sheets API" "credential" 2>/dev/null || true)"
fi
if [[ -z "$TOKEN" ]]; then
  TOKEN="$(get_keychain_secret "google-sheets-token" 2>/dev/null || true)"
fi
if [[ -z "$TOKEN" ]]; then
  log "WARN" "Token Google tidak ada. Pakai Apps Script Web App atau set GOOGLE_ACCESS_TOKEN."
  exit 0
fi

URL="https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/${SHEET_RANGE}"
RESPONSE="$(curl -sf -H "Authorization: Bearer ${TOKEN}" "$URL")"

process_queue() {
  python3 - "$RUN_TASK" <<'PY'
import json, sys, subprocess

run_task = sys.argv[1]
data = json.load(sys.stdin)
rows = data.get("values") or []

for idx, row in enumerate(rows, start=2):
    while len(row) < 5:
        row.append("")
    _id, device, command, status, args = row[0], row[1], row[2], row[3], row[4]
    if str(device).lower() not in ("mac", "all"):
        continue
    if str(status).lower() != "pending":
        continue
    if not str(command).strip():
        continue
    cmd = [run_task, str(command).strip()]
    args_str = str(args).strip()
    if args_str:
        # Pipe-separated args (e.g. whatsapp-send 628xxx|message)
        if "|" in args_str and str(command).strip() in (
            "whatsapp-send", "waha-send", "iphone-dispatch", "pushcut",
            "edtime-fetch", "edtime-sync",
        ):
            cmd.extend(args_str.split("|", 1))
        else:
            cmd.extend(args_str.split())
    print(f"EXEC row={idx} {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, timeout=600)
        print(f"DONE row={idx}")
    except subprocess.CalledProcessError as e:
        print(f"FAIL row={idx} exit={e.returncode}")
PY
}

echo "$RESPONSE" | process_queue
log "INFO" "Queue processing selesai"
