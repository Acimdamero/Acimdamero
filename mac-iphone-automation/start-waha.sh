#!/bin/bash
# Start WAHA + tampilkan QR di Terminal (Mac).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_KEY="${WAHA_API_KEY:-automation-hub-test-key}"
BASE="http://127.0.0.1:3000"

DOCKER_CMD="docker"
sudo docker info >/dev/null 2>&1 && ! docker info >/dev/null 2>&1 && DOCKER_CMD="sudo docker" || true

echo "==> Start WAHA..."
if [[ "$(uname -s)" == "Darwin" ]]; then
  open -a Docker 2>/dev/null || true
  echo "    Tunggu Docker Desktop (ikon whale)..."
  for i in $(seq 1 30); do
    $DOCKER_CMD info >/dev/null 2>&1 && break
    sleep 2
  done
fi

export WAHA_API_KEY="$API_KEY"
$DOCKER_CMD compose -f "$REPO_DIR/docker/docker-compose.waha.yml" up -d

echo "==> Tunggu WAHA ready..."
sleep 8

# Start session
curl -sf -X POST "$BASE/api/sessions/start" \
  -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"default"}' >/dev/null 2>&1 || true

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  BUKA DI BROWSER MAC:                            ║"
echo "║  http://localhost:3000/dashboard                 ║"
echo "║                                                  ║"
echo "║  Login:                                          ║"
echo "║    Username: admin                               ║"
echo "║    Password: change-me                           ║"
echo "║                                                  ║"
echo "║  Lalu: Sessions → default → lihat QR           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Poll QR
echo "==> Menunggu QR (scan dari iPhone WhatsApp → Linked Devices)..."
for i in $(seq 1 24); do
  STATUS=$(curl -sf "$BASE/api/sessions/default" -H "X-Api-Key: $API_KEY" 2>/dev/null || echo '{}')
  echo "$STATUS" | grep -q '"status":"WORKING"' && {
    echo "✅ WhatsApp TERHUBUNG!"
    exit 0
  }
  QR=$(curl -sf "$BASE/api/default/auth/qr?format=raw" -H "X-Api-Key: $API_KEY" 2>/dev/null || true)
  if [[ -n "$QR" && "$QR" != *"error"* && ${#QR} -gt 50 ]]; then
    echo ""
    echo "📱 QR CODE (scan dengan iPhone):"
    echo "$QR" | head -c 500
    echo ""
    echo "(Atau buka dashboard di browser untuk QR gambar)"
    break
  fi
  echo "   ... menunggu QR ($i/24)"
  sleep 5
done

if [[ "$(uname -s)" == "Darwin" ]]; then
  open "http://localhost:3000/dashboard" 2>/dev/null || true
fi

echo ""
echo "Scan QR: WhatsApp iPhone → Settings → Linked Devices → Link a Device"
