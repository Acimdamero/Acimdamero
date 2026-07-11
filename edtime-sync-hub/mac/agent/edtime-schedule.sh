#!/bin/bash
# LaunchAgent entry — sync edtime terjadwal (pagi + sore default).

set -euo pipefail

HUB_HOME="${EDTIME_SYNC_HOME:-$HOME/.edtime-sync}"
RUN_EDTIME="${RUN_EDTIME:-$HUB_HOME/run-edtime.sh}"
REPO_DIR="${EDTIME_REPO:-$HOME/edtime-sync-hub}"

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
  "$RUN_EDTIME" sync full >> "$HUB_HOME/logs/edtime-schedule.log" 2>&1 || \
  log "Sync failed — check edtime-monitor.sh"
log "Scheduled sync end"
