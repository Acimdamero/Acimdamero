#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config

TARGET="${1:-all}"
DEST="$(resolve_backup_dest)"
STAMP="$(date +%Y-%m-%d_%H-%M)"
DEST_RUN="$DEST/$STAMP"

mkdir -p "$DEST_RUN"

backup_path() {
  local src="$1"
  local name
  name="$(basename "$src")"
  if [[ -d "$src" ]]; then
    log "INFO" "Backing up $src -> $DEST_RUN/$name"
    rsync -a --delete "$src/" "$DEST_RUN/$name/" 2>/dev/null || rsync -a "$src/" "$DEST_RUN/$name/"
  else
    log "WARN" "Skip missing path: $src"
  fi
}

case "$TARGET" in
  documents) backup_path "$HOME/Documents" ;;
  desktop)   backup_path "$HOME/Desktop" ;;
  downloads) backup_path "$HOME/Downloads" ;;
  all)
    IFS='|' read -ra PATHS <<< "${BACKUP_SOURCES:-$HOME/Documents|$HOME/Desktop}"
    for p in "${PATHS[@]}"; do
      backup_path "$p"
    done
    ;;
  *)
    if [[ -d "$TARGET" ]]; then
      backup_path "$TARGET"
    else
      log "ERROR" "Unknown backup target: $TARGET"
      exit 1
    fi
    ;;
esac

log "INFO" "Backup selesai: $DEST_RUN"
echo "{\"status\":\"done\",\"dest\":\"$DEST_RUN\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
