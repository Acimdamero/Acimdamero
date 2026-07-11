#!/bin/bash
# Export bundle JSON edtime untuk Cursor (Mac/iOS) via Google Drive + log lokal.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=edtime-lib.sh
source "$SCRIPT_DIR/edtime-lib.sh"

LOCAL_CACHE="$HUB_HOME/edtime/processed.json"
EXPORT_DIR="$(edtime_resolve_drive_base "$EDTIME_DRIVE_FOLDER/cursor")"
EXPORT_FILE="$EXPORT_DIR/latest.json"
MAPPING="${EDTIME_MAPPING:-$HUB_HOME/edtime-mapping.json}"

usage() {
  cat <<'EOF'
edtime-export-cursor.sh — buat latest.json untuk Cursor MCP / Cursor iOS

Usage:
  edtime-export-cursor.sh [output_path]

Output:
  Google Drive/Edtime Sync/cursor/latest.json
  ~/.edtime-sync/edtime/cursor-latest.json (salinan lokal)
EOF
}

export_cursor_json() {
  local out="${1:-$EXPORT_FILE}"
  python3 - "$LOCAL_CACHE" "$MAPPING" "$out" <<'PY'
import json, sys, os
from datetime import datetime, timezone

cache_path, mapping_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
templates = {}
if os.path.isfile(mapping_path):
    with open(mapping_path) as f:
        cfg = json.load(f)
    templates = cfg.get("berichtsheft_templates", {})

schedule = []
meta = {}
if os.path.isfile(cache_path):
    with open(cache_path) as f:
        data = json.load(f)
    schedule = data.get("schedule", [])
    meta = data.get("meta", {})

def hours(start, end, br):
    from datetime import datetime, timedelta
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            s = datetime.strptime((start or "").strip(), fmt)
            e = datetime.strptime((end or "").strip(), fmt)
            if e < s:
                e += timedelta(days=1)
            return round(max(0, (e - s).total_seconds() / 3600 - float(br or 0) / 60), 2)
        except Exception:
            pass
    return 0

enriched = []
for row in schedule:
    r = dict(row)
    code = r.get("shift_code") or "default"
    tpl = templates.get(code) or templates.get("default") or "Schicht {shift_code} {start_time}-{end_time}"
    r["hours_worked"] = r.get("hours_worked") or hours(r.get("start_time"), r.get("end_time"), r.get("break_minutes"))
    try:
        r["berichtsheft_taetigkeit_template"] = tpl.format(**{**r, "shift_code": code})
    except Exception:
        r["berichtsheft_taetigkeit_template"] = tpl
    enriched.append(r)

bundle = {
    "schema": "edtime-sync/edtime-cursor-export/v1",
    "exported_at": datetime.now(timezone.utc).isoformat(),
    "source_app": "edtime Mitarbeiter-App",
    "schedule": enriched,
    "meta": meta,
    "cursor_hints": {
        "read_via": "Google Drive MCP → Edtime Sync/cursor/latest.json",
        "sheet_tab": "CursorExport",
        "next_steps": [
            "Review schedule rows",
            "Map to Berichtsheft blocks",
            "Fill narrative Tätigkeit manually if needed",
        ],
    },
}
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(bundle, f, indent=2, ensure_ascii=False)
print(out_path)
PY
}

edtime_ensure_folders
mkdir -p "$EXPORT_DIR" "$HUB_HOME/edtime"

OUT="${1:-$EXPORT_FILE}"
if [[ ! -f "$LOCAL_CACHE" ]]; then
  edtime_log "WARN" "Belum ada data — jalankan edtime-process atau edtime-sync fetch dulu"
  echo '{"schema":"edtime-sync/edtime-cursor-export/v1","schedule":[],"meta":{}}' > "$LOCAL_CACHE"
fi

RESULT="$(export_cursor_json "$OUT")"
cp "$OUT" "$HUB_HOME/edtime/cursor-latest.json"
edtime_log "INFO" "Cursor export: $RESULT"

# POST ke Sheet tab CursorExport (opsional)
if edtime_post_json "$(python3 - "$OUT" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
print(json.dumps({"action": "edtime_cursor_export", "payload": d}))
PY
)" 2>/dev/null; then
  edtime_log "INFO" "Sheet CursorExport updated"
else
  edtime_log "WARN" "Sheet POST skipped (webhook belum siap atau offline)"
fi

echo "$RESULT"
