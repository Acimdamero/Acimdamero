#!/bin/bash
# Perbaikan download WAHA macet / timeout — jalankan di Mac.
set -euo pipefail

HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.automation.docker-waha.plist"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  FIX — WAHA download macet / timeout                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. Stop proses bentrok
echo "▶ [1/5] Stop LaunchAgent sementara (cegah pull ganda)..."
launchctl unload "$PLIST" 2>/dev/null || true
pkill -f "docker-autostart.sh" 2>/dev/null || true
docker compose -f "$REPO_DIR/docker/docker-compose.waha.fast.yml" down 2>/dev/null || true

# 2. Naikkan timeout
echo "▶ [2/5] Set timeout 600 detik..."
mkdir -p "$HUB_HOME"
touch "$HUB_HOME/config.env"
grep -q '^DOCKER_START_TIMEOUT=' "$HUB_HOME/config.env" 2>/dev/null \
  && sed -i.bak 's/^DOCKER_START_TIMEOUT=.*/DOCKER_START_TIMEOUT=600/' "$HUB_HOME/config.env" \
  || echo 'DOCKER_START_TIMEOUT=600' >> "$HUB_HOME/config.env"

# 3. Restart Docker
echo "▶ [3/5] Restart Docker Desktop..."
osascript -e 'quit app "Docker"' 2>/dev/null || true
sleep 3
open -a Docker
echo "   Menunggu Docker siap..."
for i in $(seq 1 120); do docker info >/dev/null 2>&1 && break; sleep 2; done
docker info >/dev/null 2>&1 || { echo "❌ Docker belum siap — buka Docker Desktop manual"; exit 1; }
echo "   ✅ Docker siap"

# 4. Pull manual (progress terlihat)
IMAGE="devlikeapro/waha:noweb-arm"
[[ "$(uname -m)" != "arm64" ]] && IMAGE="devlikeapro/waha:noweb"
echo "▶ [4/5] Download image: $IMAGE"
echo "   (kalau angka MB naik = normal, tunggu sampai selesai)"
docker pull "$IMAGE"

# 5. Start + pair
echo "▶ [5/5] Start WAHA + pair WhatsApp..."
export WAHA_API_KEY="${WAHA_API_KEY:-automation-hub-test-key}"
export WAHA_IMAGE="$IMAGE"
docker compose -f "$REPO_DIR/docker/docker-compose.waha.fast.yml" up -d
sleep 5

launchctl load "$PLIST" 2>/dev/null || true

bash "$REPO_DIR/pair-whatsapp.sh" "agwen acim damero jerman" "Test dari Hub — fix download ✅"
