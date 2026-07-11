#!/bin/bash
# Proses data edtime: inbox Drive, screenshot metadata, normalisasi ke export lokal.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=edtime-lib.sh
source "$SCRIPT_DIR/edtime-lib.sh"

INBOX="$(edtime_resolve_drive_base "$EDTIME_DRIVE_FOLDER/inbox")"
SCREENSHOTS="$(edtime_resolve_drive_base "$EDTIME_DRIVE_FOLDER/Screenshots")"
LOCAL_CACHE="$HUB_HOME/edtime/processed.json"
PENDING_FLAG="$HUB_HOME/edtime/fetch-pending"

usage() {
  cat <<'EOF'
edtime-process.sh — proses file inbox + siapkan data untuk export Cursor

Usage:
  edtime-process.sh run              Proses semua file baru di inbox/
  edtime-process.sh check-pending    Exit 0 jika fetch masih pending
  edtime-process.sh ingest <file>    Ingest satu file JSON/CSV manual
EOF
}

merge_json_records() {
  python3 - "$LOCAL_CACHE" "$INBOX" "$SCREENSHOTS" <<'PY'
import json, os, sys, glob
from datetime import datetime, timezone
from pathlib import Path

cache_path, inbox, screenshots = sys.argv[1], sys.argv[2], sys.argv[3]
records = []
meta = {"sources": [], "screenshots": []}

if os.path.isfile(cache_path):
    try:
        with open(cache_path) as f:
            data = json.load(f)
        records = data.get("schedule", [])
        meta = data.get("meta", meta)
    except Exception:
        pass

def add_records(new_rows, source):
    for row in new_rows:
        if isinstance(row, dict):
            row.setdefault("source", source)
            row.setdefault("synced_at", datetime.now(timezone.utc).isoformat())
            records.append(row)

# Inbox: JSON files from iPhone POST mirror or manual drop
for path in sorted(glob.glob(os.path.join(inbox, "*"))):
    if path.endswith(".done"):
        continue
    try:
        if path.endswith(".json"):
            with open(path) as f:
                payload = json.load(f)
            if isinstance(payload, list):
                add_records(payload, "inbox_json")
            elif isinstance(payload, dict):
                rows = payload.get("schedule") or payload.get("rows") or [payload]
                add_records(rows, payload.get("source", "inbox_json"))
        elif path.endswith(".csv"):
            import csv
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                add_records(list(reader), "inbox_csv")
        Path(path + ".done").touch()
        meta["sources"].append({"file": os.path.basename(path), "at": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        meta.setdefault("errors", []).append({"file": path, "error": str(e)})

# Screenshot inventory (metadata only — OCR opsional di fase berikutnya)
for path in sorted(glob.glob(os.path.join(screenshots, "*"))):
    if path.lower().endswith((".png", ".jpg", ".jpeg", ".heic")):
        meta["screenshots"].append({
            "file": os.path.basename(path),
            "path": path,
            "modified": datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).isoformat(),
        })

# Dedupe by date+start+end
seen = set()
unique = []
for r in records:
    key = (r.get("date", ""), r.get("start_time", ""), r.get("end_time", ""), r.get("shift_code", ""))
    if key in seen:
        continue
    seen.add(key)
    unique.append(r)

out = {
    "schedule": unique,
    "meta": meta,
    "processed_at": datetime.now(timezone.utc).isoformat(),
}
os.makedirs(os.path.dirname(cache_path), exist_ok=True)
with open(cache_path, "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(len(unique))
PY
}

cmd="${1:-run}"
shift || true

edtime_ensure_folders
mkdir -p "$(dirname "$LOCAL_CACHE")"

case "$cmd" in
  check-pending)
    if [[ -f "$PENDING_FLAG" ]]; then
      # Flag lebih tua dari 30 menit = anggap selesai
      if [[ "$(uname -s)" == "Darwin" ]]; then
        age=$(( $(date +%s) - $(stat -f %m "$PENDING_FLAG") ))
      else
        age=$(( $(date +%s) - $(stat -c %Y "$PENDING_FLAG") ))
      fi
      if [[ "$age" -gt 1800 ]]; then
        rm -f "$PENDING_FLAG"
        exit 1
      fi
      exit 0
    fi
    exit 1
    ;;
  ingest)
    FILE="${1:?File path required}"
    cp "$FILE" "$INBOX/"
    exec "$0" run
    ;;
  run)
    rm -f "$PENDING_FLAG" 2>/dev/null || true
    COUNT="$(merge_json_records)"
    edtime_log "INFO" "Processed $COUNT schedule record(s) → $LOCAL_CACHE"

    # Pull dari Sheet jika webhook mendukung export
    if edtime_get_export "edtime-schedule" > "$HUB_HOME/edtime/sheet-export.json" 2>/dev/null; then
      python3 - "$LOCAL_CACHE" "$HUB_HOME/edtime/sheet-export.json" <<'PY'
import json, sys
cache_p, sheet_p = sys.argv[1], sys.argv[2]
with open(cache_p) as f:
    cache = json.load(f)
with open(sheet_p) as f:
    sheet = json.load(f)
rows = sheet.get("schedule") or sheet.get("rows") or []
if rows:
    cache["schedule"].extend(rows)
    seen = set()
    uniq = []
    for r in cache["schedule"]:
        k = (r.get("date"), r.get("start_time"), r.get("end_time"))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    cache["schedule"] = uniq
    cache["meta"]["sheet_merge"] = True
    with open(cache_p, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    print(f"merged {len(rows)} from sheet")
PY
      edtime_log "INFO" "Merged Sheet export"
    fi
    ;;
  *)
    usage
    exit 1
    ;;
esac
