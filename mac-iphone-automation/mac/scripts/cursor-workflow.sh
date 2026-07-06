#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

ACTION="${1:?Action required}"
PROJECT_DIR="${2:?Project directory required}"

if [[ ! -d "$PROJECT_DIR" ]]; then
  log "ERROR" "Directory tidak ditemukan: $PROJECT_DIR"
  exit 1
fi

cd "$PROJECT_DIR"

case "$ACTION" in
  cursor-pull)
    log "INFO" "Git pull: $PROJECT_DIR"
    git pull --ff-only
    ;;
  cursor-build)
    log "INFO" "Build: $PROJECT_DIR"
    if [[ -f package.json ]]; then
      if command -v pnpm >/dev/null 2>&1; then
        pnpm install && pnpm run build
      elif command -v npm >/dev/null 2>&1; then
        npm install && npm run build
      else
        log "ERROR" "npm/pnpm tidak ditemukan"
        exit 1
      fi
    else
      log "ERROR" "package.json tidak ditemukan di $PROJECT_DIR"
      exit 1
    fi
    ;;
  *)
    log "ERROR" "Unknown cursor action: $ACTION"
    exit 1
    ;;
esac

echo "{\"status\":\"done\",\"action\":\"$ACTION\",\"project\":\"$PROJECT_DIR\"}"
