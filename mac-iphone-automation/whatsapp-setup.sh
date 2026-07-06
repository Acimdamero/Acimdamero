#!/bin/bash
# Setup WhatsApp otomatis dari nol — clone repo (jika perlu) + install + pair.
# Usage: bash whatsapp-setup.sh

set -euo pipefail

REPO_URL="${AUTOMATION_REPO_URL:-https://github.com/Acimdamero/Acimdamero.git}"
BRANCH="${AUTOMATION_BRANCH:-cursor/mac-iphone-automation-hub-8703}"
TARGET="${AUTOMATION_TARGET:-$HOME/Acimdamero/Acimdamero}"
HUB_DIR="$TARGET/mac-iphone-automation"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     WHATSAPP SETUP — dari nol sampai bisa kirim           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

[[ "$(uname -s)" != "Darwin" ]] && {
  echo "⚠️  Script ini untuk MacBook. Clone manual lalu bash pair-whatsapp.sh"
  exit 1
}

# ── 1. Clone repo jika belum ada ───────────────────────────────
echo "▶ [1/4] Cek repository..."
if [[ ! -f "$HUB_DIR/pair-whatsapp.sh" ]]; then
  echo "   Repo belum ada — clone ke $TARGET"
  mkdir -p "$(dirname "$TARGET")"
  if [[ -d "$TARGET/.git" ]]; then
    cd "$TARGET"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
  else
    git clone --branch "$BRANCH" "$REPO_URL" "$TARGET"
  fi
else
  echo "   ✅ Repo sudah ada: $HUB_DIR"
  cd "$TARGET"
  git fetch origin 2>/dev/null && git pull origin "$BRANCH" 2>/dev/null || true
fi

cd "$HUB_DIR"

# ── 2. Download WAHA cepat (image ringan) ──────────────────────
echo "▶ [2/4] Download WAHA (versi ringan, lebih cepat)..."
bash "$HUB_DIR/pull-waha-fast.sh"

# ── 3. Install hub agent ───────────────────────────────────────
echo "▶ [3/4] Install hub agent..."
bash "$HUB_DIR/mac/install.sh"

# ── 4. Pair WhatsApp + test kirim ──────────────────────────────
echo "▶ [4/4] Pair WhatsApp..."
bash "$HUB_DIR/pair-whatsapp.sh" \
  "agwen acim damero jerman" \
  "🤖 Test Automation Hub — WhatsApp otomatis dari Mac ✅"
