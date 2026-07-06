#!/bin/bash
# Download WAHA image ringan + start — progress terlihat di terminal.
# Mac M1/M2/M3: pakai noweb-arm (~700MB, tanpa Chromium)
# Intel Mac: pakai noweb (~720MB)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_KEY="${WAHA_API_KEY:-automation-hub-test-key}"
COMPOSE_FILE="$REPO_DIR/docker/docker-compose.waha.fast.yml"

if [[ "$(uname -m)" == "arm64" ]]; then
  IMAGE="devlikeapro/waha:noweb-arm"
else
  IMAGE="devlikeapro/waha:noweb"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  WAHA FAST PULL — image ringan, progress terlihat        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Image: $IMAGE"
echo "Ukuran: ~700MB (vs ~1GB untuk versi Chromium)"
echo ""

# Stop proses lama jika ada
docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
docker rm -f automation-hub-waha 2>/dev/null || true

echo "▶ [1/3] Download image (progress di bawah)..."
echo "   Tips: pakai WiFi stabil / hotspot 4G kalau WiFi lambat"
echo ""
docker pull "$IMAGE"

echo ""
echo "▶ [2/3] Start container..."
export WAHA_API_KEY="$API_KEY"
export WAHA_IMAGE="$IMAGE"
docker compose -f "$COMPOSE_FILE" up -d

sleep 5
docker ps | grep automation-hub-waha && echo "   ✅ Container jalan" || {
  echo "   ❌ Container gagal start"
  docker logs automation-hub-waha --tail 20
  exit 1
}

echo ""
echo "▶ [3/3] Cek http://localhost:3000 ..."
curl -s -o /dev/null -w "   HTTP %{http_code}\n" http://127.0.0.1:3000/ || true

echo ""
echo "✅ WAHA siap! Lanjut pair WhatsApp:"
echo "   bash pair-whatsapp.sh"
echo ""
