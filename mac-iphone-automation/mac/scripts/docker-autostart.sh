#!/bin/bash
# Auto-start Docker Desktop + WAHA — tanpa buka manual.
# Dipanggil oleh LaunchAgent saat login Mac.

set -euo pipefail

HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
CONFIG="${HUB_CONFIG:-$HUB_HOME/config.env}"
LOG="$HUB_HOME/logs/docker-autostart.log"

mkdir -p "$HUB_HOME/logs"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

[[ -f "$CONFIG" ]] && source "$CONFIG" 2>/dev/null || true

REPO_DIR="${AUTOMATION_REPO:-$HOME/Acimdamero/mac-iphone-automation}"
COMPOSE_FILE="${WAHA_COMPOSE_FILE:-$REPO_DIR/docker/docker-compose.waha.yml}"
# Mac Apple Silicon: pakai image ringan (noweb-arm) secara default
if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" && -z "${WAHA_COMPOSE_FILE:-}" ]]; then
  FAST="$REPO_DIR/docker/docker-compose.waha.fast.yml"
  [[ -f "$FAST" ]] && COMPOSE_FILE="$FAST"
fi
API_KEY="${WAHA_API_KEY:-automation-hub-test-key}"
MAX_WAIT="${DOCKER_START_TIMEOUT:-120}"

# Skip jika dimatikan
[[ "${DOCKER_AUTOSTART:-1}" == "0" ]] && { log "DOCKER_AUTOSTART=0, skip"; exit 0; }

[[ "$(uname -s)" != "Darwin" ]] && { log "Bukan macOS, skip"; exit 0; }

docker_ready() {
  docker info >/dev/null 2>&1
}

start_docker_desktop() {
  if docker_ready; then
    log "Docker sudah jalan"
    return 0
  fi

  log "Membuka Docker Desktop..."
  open -a Docker 2>/dev/null || open -ga "Docker" 2>/dev/null || {
    log "ERROR: Docker Desktop tidak ditemukan. Install dari docker.com"
    exit 1
  }

  log "Menunggu Docker siap (max ${MAX_WAIT}s)..."
  for ((i=1; i<=MAX_WAIT; i++)); do
    if docker_ready; then
      log "✅ Docker siap (${i}s)"
      return 0
    fi
    sleep 1
  done

  log "ERROR: Docker timeout setelah ${MAX_WAIT}s"
  exit 1
}

start_waha() {
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    log "WARN: compose tidak ada: $COMPOSE_FILE"
    return 1
  fi

  export WAHA_API_KEY="$API_KEY"
  log "Start WAHA container..."
  if [[ -t 1 ]] || [[ "${SHOW_DOCKER_OUTPUT:-0}" == "1" ]]; then
    log "   (download image pertama kali bisa 5-15 menit — tunggu...)"
    docker compose -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG"
  else
    docker compose -f "$COMPOSE_FILE" up -d >>"$LOG" 2>&1
  fi

  sleep 5

  if docker ps --format '{{.Names}}' | grep -q automation-hub-waha; then
    log "✅ WAHA container running"
  else
    log "ERROR: WAHA container gagal start"
    return 1
  fi

  # Start WhatsApp session (QR jika belum pernah scan)
  curl -sf -X POST "http://127.0.0.1:3000/api/sessions/start" \
    -H "X-Api-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"name":"default"}' >>"$LOG" 2>&1 || true

  STATUS=$(curl -sf "http://127.0.0.1:3000/api/sessions/default" \
    -H "X-Api-Key: $API_KEY" 2>/dev/null || echo '{}')
  log "Session status: $STATUS"

  if [[ "$(uname -s)" == "Darwin" ]] && [[ "${OPEN_WAHA_DASHBOARD:-0}" == "1" ]]; then
    open "http://localhost:3000/dashboard" 2>/dev/null || true
  fi
}

log "=== Docker autostart begin ==="
start_docker_desktop
start_waha
log "=== Docker autostart done ==="
