#!/bin/bash
# LaunchAgent entry — sync edtime terjadwal (pagi + sore default).

set -euo pipefail

HUB_HOME="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
RUN_TASK="${RUN_TASK:-$HUB_HOME/run-task.sh}"
REPO_DIR="${AUTOMATION_REPO:-$HOME/Acimdamero/mac-iphone-automation}"

if [[ -f "$HUB_HOME/config.env" ]]; then
  # shellcheck disable=SC1090
  source "$HUB_HOME/config.env"
fi

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [edtime-schedule] $*" >> "$HUB_HOME/logs/edtime-schedule.log"
}

log "Scheduled sync start"
export EDTIME_RUN_SYNC=1
bash "$REPO_DIR/mac/scripts/edtime-agent-orchestrator.sh" sync >> "$HUB_HOME/logs/edtime-schedule.log" 2>&1 || \
  "$RUN_TASK" edtime-sync full >> "$HUB_HOME/logs/edtime-schedule.log" 2>&1 || \
  log "Sync failed — check edtime-monitor.sh"
log "Scheduled sync end"
