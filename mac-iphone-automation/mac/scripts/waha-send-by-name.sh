#!/bin/bash
# Cari kontak WAHA by name (partial match) lalu kirim pesan test.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

SEARCH_NAME="${1:?Contact name search required, e.g. 'agwen acim damero jerman'}"
MESSAGE="${2:-🤖 Test Automation Hub — pesan otomatis berhasil.}"

BASE_URL="${WAHA_BASE_URL:-http://localhost:3000}"
SESSION="${WAHA_SESSION:-default}"
API_KEY="${WAHA_API_KEY:-}"

if [[ -z "$API_KEY" ]]; then
  API_KEY="$(get_keychain_secret "waha-api-key" 2>/dev/null || true)"
fi

HEADERS=()
if [[ -n "$API_KEY" ]]; then
  HEADERS+=(-H "X-Api-Key: ${API_KEY}")
fi

log "INFO" "Mencari kontak: $SEARCH_NAME"

CONTACTS_JSON=$(curl -sf "${HEADERS[@]}" \
  "${BASE_URL}/api/contacts/all?session=${SESSION}&limit=500&sortBy=name&sortOrder=asc")

MATCH=$(python3 - "$SEARCH_NAME" "$CONTACTS_JSON" <<'PY'
import json, sys, re

query = sys.argv[1].lower().strip()
raw = sys.argv[2]
words = [w for w in re.split(r"\s+", query) if len(w) > 2]

try:
    contacts = json.loads(raw)
except Exception:
    print("ERROR:invalid_json")
    sys.exit(0)

if not isinstance(contacts, list):
    print("ERROR:not_list")
    sys.exit(0)

def score(c):
    fields = " ".join([
        str(c.get("name") or ""),
        str(c.get("pushname") or ""),
        str(c.get("shortName") or ""),
    ]).lower()
    if query in fields:
        return 100
    return sum(1 for w in words if w in fields)

best = None
best_score = 0
for c in contacts:
    if c.get("isGroup"):
        continue
    s = score(c)
    if s > best_score:
        best_score = s
        best = c

if not best or best_score == 0:
    print("NOTFOUND")
else:
    cid = best.get("id") or f"{best.get('number')}@c.us"
    name = best.get("name") or best.get("pushname") or cid
    print(f"FOUND|{cid}|{name}|{best_score}")
PY
)

if [[ "$MATCH" == NOTFOUND ]]; then
  log "ERROR" "Kontak tidak ditemukan untuk: $SEARCH_NAME"
  log "ERROR" "Pastikan WAHA session aktif & kontak ada di WhatsApp"
  exit 1
fi

if [[ "$MATCH" == ERROR:* ]]; then
  log "ERROR" "Gagal baca kontak WAHA — cek docker & session"
  exit 1
fi

CHAT_ID=$(echo "$MATCH" | cut -d'|' -f2)
FOUND_NAME=$(echo "$MATCH" | cut -d'|' -f3)

log "INFO" "Kontak ditemukan: $FOUND_NAME ($CHAT_ID)"
PHONE="${CHAT_ID/@c.us/}"
exec "$SCRIPT_DIR/waha-send.sh" "$PHONE" "$MESSAGE"
