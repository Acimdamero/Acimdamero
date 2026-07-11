#!/bin/bash
# Dispatch perintah ke iPhone via Google Sheet Queue (POST webhook).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=edtime-lib.sh
source "$SCRIPT_DIR/edtime-lib.sh"

COMMAND="${1:?command e.g. edtime-fetch}"
ARGS="${2:-}"

payload=$(python3 - "$COMMAND" "$ARGS" <<'PY'
import json, sys
print(json.dumps({"device": "iphone", "command": sys.argv[1], "args": sys.argv[2]}))
PY
)

edtime_log "INFO" "Queue iphone: $COMMAND $ARGS"
edtime_post_json "$payload"
