#!/bin/bash
# Langkah manual paling sederhana — tanpa restart Docker.
# Usage: bash lanjut-waha.sh

set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "=== LANJUT WAHA (manual, tanpa restart Docker) ==="
echo ""

# Cek docker
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker belum jalan!"
  echo "   1. Buka Docker Desktop dari Applications"
  echo "   2. Tunggu ikon paus HIJAU di menu bar"
  echo "   3. Jalankan lagi: bash lanjut-waha.sh"
  exit 1
fi
echo "✅ Docker jalan"

# Stop launchagent bentrok
launchctl unload "$HOME/Library/LaunchAgents/com.automation.docker-waha.plist" 2>/dev/null || true

# Pull + start
bash "$REPO_DIR/pull-waha-fast.sh"

# Pair
bash "$REPO_DIR/pair-whatsapp.sh" "agwen acim damero jerman" "Test dari Hub ✅"
