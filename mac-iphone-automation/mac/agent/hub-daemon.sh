#!/bin/bash
# Daemon ringan — polling antrian Google Sheet + update status Mac.

set -euo pipefail

HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
CONFIG_FILE="${HUB_CONFIG:-$HUB_HOME/config.env}"
RUN_TASK="${RUN_TASK:-$HUB_HOME/run-task.sh}"
POLL="${POLL_INTERVAL_SECONDS:-60}"

if [[ -f "$CONFIG_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
fi

export RUN_TASK

log_daemon() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [daemon] $*"
}

log_daemon "Automation Hub daemon started (poll=${POLL}s)"

while true; do
  "$RUN_TASK" status >/dev/null 2>&1 || true
  "$RUN_TASK" queue-process 2>&1 | while read -r line; do
    log_daemon "$line"
  done
  sleep "$POLL"
done
