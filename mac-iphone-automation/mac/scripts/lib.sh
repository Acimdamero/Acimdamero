#!/bin/bash
# Library bersama untuk script otomatisasi Mac.

set -euo pipefail

HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
CONFIG_FILE="${HUB_CONFIG:-$HUB_HOME/config.env}"
LOG_DIR="${HUB_LOG_DIR:-$HUB_HOME/logs}"

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
  echo "$msg" >> "$LOG_DIR/hub.log"
}

# Ambil secret dari 1Password CLI (jika terpasang)
get_op_secret() {
  local item="$1"
  local field="${2:-password}"
  if command -v op >/dev/null 2>&1; then
    op read "op://${OP_VAULT:-Private}/${item}/${field}" 2>/dev/null || return 1
  fi
  return 1
}

# Ambil secret dari Apple Keychain
get_keychain_secret() {
  local account="$1"
  local service="${KEYCHAIN_SERVICE:-automation-hub}"
  security find-generic-password -s "$service" -a "$account" -w 2>/dev/null || return 1
}

resolve_backup_dest() {
  local pattern="${BACKUP_DEST:-$HOME/Google Drive/Automation Hub/Backups}"
  # Expand glob pertama yang cocok (Google Drive path bervariasi per akun)
  for path in $pattern; do
    if [[ -d "$path" || -d "$(dirname "$path")" ]]; then
      echo "$path"
      return 0
    fi
  done
  echo "$HUB_HOME/backups"
}
