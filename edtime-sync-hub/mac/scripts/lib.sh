#!/bin/bash
# Library edtime-sync-hub

set -euo pipefail

SYNC_HOME="${EDTIME_SYNC_HOME:-$HOME/.edtime-sync}"
CONFIG_FILE="${EDTIME_CONFIG:-$SYNC_HOME/config.env}"
LOG_DIR="${EDTIME_LOG_DIR:-$SYNC_HOME/logs}"
KEYCHAIN_SERVICE="${KEYCHAIN_SERVICE:-edtime-sync}"

load_config() {
  if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
  fi
}

ensure_log_dir() {
  mkdir -p "$LOG_DIR"
}

log() {
  ensure_log_dir
  local level="$1"
  shift
  local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*"
  echo "$msg"
  echo "$msg" >> "$LOG_DIR/edtime.log"
}

get_keychain_secret() {
  local account="$1"
  security find-generic-password -s "$KEYCHAIN_SERVICE" -a "$account" -w 2>/dev/null || return 1
}

resolve_drive_base() {
  for path in "$HOME/Library/CloudStorage/GoogleDrive-"*; do
    [[ -d "$path" ]] && echo "$path" && return 0
  done
  echo "$SYNC_HOME/drive"
}
