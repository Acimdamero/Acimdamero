#!/bin/bash
# Setup otomatis pipeline edtime: Keychain, folder Drive, mapping, Sheet tabs, Shortcuts guide.
# Mode non-interaktif: bash setup-edtime-sync.sh --non-interactive
#                      atau AUTONOMOUS=1 HUB_WEBHOOK_URL=... GOOGLE_SHEET_ID=...

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${EDTIME_SYNC_HOME:-$HOME/.edtime-sync}"
SCRIPTS="$HUB_HOME/scripts"
NON_INTERACTIVE=0

for arg in "$@"; do
  case "$arg" in
    --non-interactive|--yes|-y) NON_INTERACTIVE=1 ;;
  esac
done
[[ "${AUTONOMOUS:-0}" == "1" ]] && NON_INTERACTIVE=1

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  edtime Sync Setup — iPhone → Sheet/Drive → Cursor       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Install scripts jika belum
if [[ ! -x "$HUB_HOME/run-edtime.sh" ]]; then
  echo "==> edtime-sync-hub belum terinstall — menjalankan mac/install.sh..."
  bash "$REPO_DIR/mac/install.sh"
fi

mkdir -p "$HUB_HOME"/{edtime,logs,agent}
chmod +x "$REPO_DIR/mac/scripts/"edtime-*.sh 2>/dev/null || true
cp -f "$REPO_DIR/mac/scripts/edtime-"*.sh "$SCRIPTS/" 2>/dev/null || true
cp -f "$REPO_DIR/mac/agent/edtime-schedule.sh" "$HUB_HOME/agent/" 2>/dev/null || true
chmod +x "$SCRIPTS"/edtime-*.sh "$HUB_HOME/agent/edtime-schedule.sh" 2>/dev/null || true

# Mapping config
if [[ ! -f "$HUB_HOME/edtime-mapping.json" ]]; then
  cp "$REPO_DIR/config/edtime-mapping.json.example" "$HUB_HOME/edtime-mapping.json"
  echo "✓ edtime-mapping.json dibuat di $HUB_HOME/edtime-mapping.json"
else
  echo "✓ edtime-mapping.json sudah ada"
fi

# Patch config.env
CONFIG="$HUB_HOME/config.env"
touch "$CONFIG"
grep -q '^EDTIME_DRIVE_FOLDER=' "$CONFIG" 2>/dev/null || \
  echo 'EDTIME_DRIVE_FOLDER="Edtime Sync"' >> "$CONFIG"
grep -q '^EDTIME_FETCH_TIMEOUT=' "$CONFIG" 2>/dev/null || \
  echo 'EDTIME_FETCH_TIMEOUT=900' >> "$CONFIG"
grep -q '^EDTIME_NOTIFY_ON_COMPLETE=' "$CONFIG" 2>/dev/null || \
  echo 'EDTIME_NOTIFY_ON_COMPLETE=1' >> "$CONFIG"
grep -q '^EDTIME_MAPPING=' "$CONFIG" 2>/dev/null || \
  echo "EDTIME_MAPPING=$HUB_HOME/edtime-mapping.json" >> "$CONFIG"
echo "✓ config.env diperbarui"

# Drive folders
DRIVE_BASE=""
for path in "$HOME/Library/CloudStorage/GoogleDrive-"*; do
  if [[ -d "$path" ]]; then
    DRIVE_BASE="$path"
    break
  fi
done
if [[ -n "$DRIVE_BASE" ]]; then
  mkdir -p "$DRIVE_BASE/Edtime Sync"/{Screenshots,inbox,cursor}
  echo "✓ Folder Drive: $DRIVE_BASE/Edtime Sync/"
else
  echo "⚠ Google Drive Desktop belum terdeteksi — folder akan dibuat saat Drive terpasang"
  mkdir -p "$HUB_HOME/edtime"/{Screenshots,inbox,cursor}
fi

echo ""
echo "── Webhook Apps Script ──"
WEBHOOK_URL="${HUB_WEBHOOK_URL:-${EDTIME_WEBHOOK_URL:-}}"
if [[ "$NON_INTERACTIVE" == "1" ]]; then
  if [[ -n "$WEBHOOK_URL" ]]; then
    bash "$SCRIPTS/edtime-save-credentials.sh" webhook "$WEBHOOK_URL"
    echo "✓ Webhook disimpan (non-interactive)"
    curl -sfL "${WEBHOOK_URL%%\?*}?action=setup-edtime" >/dev/null 2>&1 && \
      echo "✓ Sheet tabs edtime diinisialisasi via Apps Script" || \
      echo "⚠ setup-edtime API belum deploy — paste EdtimeWebApp.gs & redeploy"
  else
    echo "⚠ HUB_WEBHOOK_URL belum diset — lewati Keychain webhook"
  fi
else
  echo "Deploy EdtimeWebApp.gs dari:"
  echo "  $REPO_DIR/google/apps-script/EdtimeWebApp.gs"
  echo ""
  read -r -p "Paste Web App URL (Enter untuk lewati): " WEBHOOK_URL || true
  if [[ -n "${WEBHOOK_URL:-}" ]]; then
    bash "$SCRIPTS/edtime-save-credentials.sh" webhook "$WEBHOOK_URL"
    echo "✓ Webhook disimpan di Keychain"
    curl -sfL "${WEBHOOK_URL%%\?*}?action=setup-edtime" >/dev/null 2>&1 && \
      echo "✓ Sheet tabs edtime diinisialisasi" || true
  fi
fi

if [[ "$NON_INTERACTIVE" == "1" ]]; then
  [[ -n "${EDTIME_USER:-}" ]] && bash "$SCRIPTS/edtime-save-credentials.sh" edtime-user "$EDTIME_USER" || true
else
  echo ""
  read -r -p "edtime username/email (opsional, Enter lewati): " EDTIME_USER || true
  if [[ -n "${EDTIME_USER:-}" ]]; then
    bash "$SCRIPTS/edtime-save-credentials.sh" edtime-user "$EDTIME_USER"
  fi
fi

echo ""
echo "── Google Sheet ──"
SHEET_ID="${GOOGLE_SHEET_ID:-}"
if [[ "$NON_INTERACTIVE" == "1" ]]; then
  if [[ -n "$SHEET_ID" ]]; then
    if grep -q '^GOOGLE_SHEET_ID=' "$CONFIG"; then
      sed -i.bak "s|^GOOGLE_SHEET_ID=.*|GOOGLE_SHEET_ID=$SHEET_ID|" "$CONFIG"
    else
      echo "GOOGLE_SHEET_ID=$SHEET_ID" >> "$CONFIG"
    fi
    echo "✓ GOOGLE_SHEET_ID disimpan"
  fi
else
  echo "Buat tab — lihat: $REPO_DIR/google/SHEET-EDTIME-TABS.md"
  read -r -p "GOOGLE_SHEET_ID (Enter lewati): " SHEET_ID || true
  if [[ -n "${SHEET_ID:-}" ]]; then
    if grep -q '^GOOGLE_SHEET_ID=' "$CONFIG"; then
      sed -i.bak "s|^GOOGLE_SHEET_ID=.*|GOOGLE_SHEET_ID=$SHEET_ID|" "$CONFIG"
    else
      echo "GOOGLE_SHEET_ID=$SHEET_ID" >> "$CONFIG"
    fi
    echo "✓ GOOGLE_SHEET_ID disimpan"
  fi
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Langkah iPhone (wajib — sekali)                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "1. Login edtime app manual (session tersimpan di iPhone)"
echo "2. Buat Shortcuts — ikuti:"
echo "   $REPO_DIR/iphone/EDTIME-SHORTCUTS-SETUP.md"
echo "3. Automation: Poll queue tiap 15 menit ATAU pasang Pushcut"
echo "4. Aktifkan Google Drive di iPhone (app sama dengan Mac)"
echo ""
echo "── Test dari Mac ──"
echo "  $HUB_HOME/run-edtime.sh open"
echo "  $HUB_HOME/run-edtime.sh fetch week=current"
echo "  $HUB_HOME/run-edtime.sh sync full"
echo "  $HUB_HOME/run-edtime.sh export"
echo ""
echo "── Cursor iOS / MCP ──"
echo "  Baca: Drive → Edtime Sync/cursor/latest.json"
echo "  Panduan: $REPO_DIR/docs/SETUP.md"
echo ""
echo "Setup selesai."
