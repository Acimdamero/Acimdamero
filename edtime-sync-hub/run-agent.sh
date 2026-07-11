#!/bin/bash
# Agentic setup edtime-sync-hub — satu perintah.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_HOME="${EDTIME_SYNC_HOME:-$HOME/.edtime-sync}"
SECRETS="$SYNC_HOME/secrets.env"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Edtime Sync Hub — Agentic Setup                         ║"
echo "╚══════════════════════════════════════════════════════════╝"

if [[ ! -f "$SECRETS" ]]; then
  bash "$REPO_DIR/install-secrets.sh"
  if [[ ! -f "$SECRETS" ]] || ! grep -q '^GOOGLE_SHEET_ID=.' "$SECRETS"; then
    echo "Isi GOOGLE_SHEET_ID di $SECRETS lalu jalankan ulang."
    exit 1
  fi
fi

# shellcheck disable=SC1090
source "$SECRETS"

[[ -n "${GOOGLE_SHEET_ID:-}" ]] || { echo "GOOGLE_SHEET_ID kosong"; exit 1; }

export AUTONOMOUS=1
bash "$REPO_DIR/mac/install.sh"
bash "$REPO_DIR/setup-edtime-sync.sh" --non-interactive 2>/dev/null || true
bash "$SYNC_HOME/scripts/edtime-agent-orchestrator.sh" run 2>/dev/null || \
  bash "$REPO_DIR/mac/scripts/edtime-agent-orchestrator.sh" run

bash "$REPO_DIR/test-edtime-pipeline.sh" || true
"$SYNC_HOME/scripts/edtime-monitor.sh" status 2>/dev/null || \
  bash "$REPO_DIR/mac/scripts/edtime-monitor.sh" status

echo ""
echo "Selesai. Monitor: ~/.edtime-sync/run-edtime.sh monitor watch"
