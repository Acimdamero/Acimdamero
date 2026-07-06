#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

load_config
ensure_log_dir

HOSTNAME="$(scutil --get ComputerName 2>/dev/null || hostname)"
UPTIME="$(uptime | sed 's/^.*up/up/')"
DISK="$(df -h / | awk 'NR==2 {print $5 " used, " $4 " free"}')"

BATTERY=""
if pmset -g batt 2>/dev/null | grep -q "Battery"; then
  BATTERY="$(pmset -g batt | grep -Eo '[0-9]+%')"
fi

WIFI=""
if /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I 2>/dev/null | grep -q " SSID"; then
  WIFI="$(/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I 2>/dev/null | awk -F': ' '/ SSID/{print $2}')"
fi

JSON_FILE="$LOG_DIR/last-status.json"
cat > "$JSON_FILE" <<EOF
{
  "device": "mac",
  "hostname": "$HOSTNAME",
  "uptime": "$UPTIME",
  "disk": "$DISK",
  "battery": "$BATTERY",
  "wifi": "$WIFI",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

log "INFO" "Status: $HOSTNAME | $DISK | battery=$BATTERY"
cat "$JSON_FILE"
