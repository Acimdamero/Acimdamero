#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# RUN EDtime AGENTIC — satu perintah, setup + sync otomatis penuh
# Anda hanya: isi secrets.env SEKALI → monitor → test → putuskan
# Usage:
#   cp config/secrets.example.env ~/.automation-hub/secrets.env
#   # edit GOOGLE_SHEET_ID + HUB_WEBHOOK_URL
#   bash run-edtime-agentic.sh
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
SECRETS="$HUB_HOME/secrets.env"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  EDtime AGENTIC SETUP — otomatis penuh                   ║"
echo "║  Anda: monitor + keputusan + test saja                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 0. Secrets template ─────────────────────────────────────────
if [[ ! -f "$SECRETS" ]]; then
  mkdir -p "$HUB_HOME"
  cp "$REPO_DIR/config/secrets.example.env" "$SECRETS"
  echo "📝 Dibuat: $SECRETS"
  echo ""
  echo "   ⚠️  ISI DULU (2 baris wajib):"
  echo "      GOOGLE_SHEET_ID=..."
  echo "      HUB_WEBHOOK_URL=..."
  echo ""
  echo "   Lalu jalankan ulang: bash run-edtime-agentic.sh"
  echo ""
  if [[ "${AUTONOMOUS:-0}" != "1" ]]; then
    exit 0
  fi
fi

# shellcheck disable=SC1090
source "$SECRETS" 2>/dev/null || true

# Validasi minimal
MISSING=0
if [[ -z "${GOOGLE_SHEET_ID:-}" ]]; then
  echo "❌ GOOGLE_SHEET_ID kosong di $SECRETS"
  MISSING=1
fi
if [[ -z "${HUB_WEBHOOK_URL:-}" ]]; then
  echo "❌ HUB_WEBHOOK_URL kosong di $SECRETS"
  echo "   Deploy Apps Script (QueueSync.gs + EdtimeSync.gs) → Web App URL"
  MISSING=1
fi
if [[ "$MISSING" == "1" ]]; then
  echo ""
  echo "Setelah diisi, jalankan: bash run-edtime-agentic.sh"
  exit 1
fi

export AUTONOMOUS=1
export EDTIME_RUN_SYNC="${EDTIME_RUN_SYNC:-1}"

# ── 1. Base hub (non-interactive) ───────────────────────────────
echo "▶ [1/5] Install Automation Hub..."
bash "$REPO_DIR/install-all.sh" 2>&1 | tail -20

# ── 2. edtime scripts + config ──────────────────────────────────
echo ""
echo "▶ [2/5] Setup edtime sync (non-interactive)..."
bash "$REPO_DIR/setup-edtime-sync.sh" --non-interactive

# ── 3. Agentic orchestrator ───────────────────────────────────
echo ""
echo "▶ [3/5] Agent orchestrator (install → configure → daemon → sync)..."
chmod +x "$REPO_DIR/mac/scripts/edtime-agent-orchestrator.sh"
chmod +x "$REPO_DIR/mac/scripts/edtime-monitor.sh"
chmod +x "$REPO_DIR/mac/agent/edtime-schedule.sh"
bash "$REPO_DIR/mac/scripts/edtime-agent-orchestrator.sh" run

# ── 4. Test pipeline ────────────────────────────────────────────
echo ""
echo "▶ [4/5] Test edtime pipeline..."
bash "$REPO_DIR/test-edtime-pipeline.sh" || true

# ── 5. Monitor dashboard ────────────────────────────────────────
echo ""
echo "▶ [5/5] Monitor dashboard..."
"$HUB_HOME/scripts/edtime-monitor.sh" status 2>/dev/null || \
  bash "$REPO_DIR/mac/scripts/edtime-monitor.sh" status

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ AGENTIC SETUP SELESAI                                 ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Monitor:  bash mac/scripts/edtime-monitor.sh watch      ║"
echo "║  Test:     bash test-edtime-pipeline.sh                  ║"
echo "║  Manual:   ~/.automation-hub/run-task.sh edtime-sync full║"
echo "║  Cursor:   Drive/Edtime/cursor/latest.json               ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  ANDA PERLU (sekali):                                    ║"
echo "║  • iPhone Shortcuts (EDTIME-SHORTCUTS-SETUP.md)          ║"
echo "║  • Login edtime + SS saat fetch pertama                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
