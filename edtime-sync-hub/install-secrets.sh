#!/bin/bash
# Install secrets.env ke Mac — tanpa nano manual.
# Usage: bash install-secrets.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${EDTIME_SYNC_HOME:-$HOME/.edtime-sync}"
SRC="$REPO_DIR/config/secrets.ready.env"
DEST="$HUB_HOME/secrets.env"

mkdir -p "$HUB_HOME"

if [[ -f "$DEST" ]] && grep -q '^HUB_WEBHOOK_URL=https' "$DEST" 2>/dev/null; then
  echo "✓ secrets.env sudah ada dengan webhook — tidak ditimpa"
  echo "  Lokasi: $DEST"
  exit 0
fi

cp "$SRC" "$DEST"
chmod 600 "$DEST"

# Sync ke config.env juga
grep -q '^GOOGLE_SHEET_ID=' "$HUB_HOME/config.env" 2>/dev/null || \
  touch "$HUB_HOME/config.env"
if [[ -f "$HUB_HOME/config.env" ]]; then
  SID="$(grep '^GOOGLE_SHEET_ID=' "$DEST" | cut -d= -f2-)"
  if grep -q '^GOOGLE_SHEET_ID=' "$HUB_HOME/config.env"; then
    sed -i.bak "s|^GOOGLE_SHEET_ID=.*|GOOGLE_SHEET_ID=$SID|" "$HUB_HOME/config.env" 2>/dev/null || true
  else
    echo "GOOGLE_SHEET_ID=$SID" >> "$HUB_HOME/config.env"
  fi
fi

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  secrets.env TERINSTALL                                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Lokasi file: $DEST"
echo ""
echo "  GOOGLE_SHEET_ID = sudah diisi ✓"
echo "  HUB_WEBHOOK_URL = masih kosong (isi setelah deploy Apps Script)"
echo ""
echo "  Buka di Cursor: File → Open → $DEST"
echo "  Atau Terminal:  open -e $DEST"
echo ""
echo "  Setelah deploy Apps Script, isi webhook:"
echo "    bash $REPO_DIR/set-webhook-url.sh 'URL_WEB_APP_ANDA'"
echo ""
