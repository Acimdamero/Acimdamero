#!/bin/bash
# Test pipeline edtime — mock data jika fetch iPhone belum selesai.

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}"
SCRIPTS="$HUB/scripts"
PASS=0
FAIL=0

ok()  { echo "  ✅ $1"; PASS=$((PASS+1)); }
bad() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  EDtime Pipeline Test                                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "▶ Scripts"
[[ -x "$SCRIPTS/edtime-sync.sh" ]] || [[ -x "$REPO_DIR/mac/scripts/edtime-sync.sh" ]] \
  && ok "edtime-sync.sh" || bad "edtime-sync.sh missing"
[[ -f "$REPO_DIR/mac/scripts/edtime-agent-orchestrator.sh" ]] && ok "orchestrator" || bad "orchestrator"
[[ -f "$REPO_DIR/run-edtime-agentic.sh" ]] && ok "run-edtime-agentic.sh" || bad "run-edtime-agentic"

echo ""
echo "▶ Mock ingest + export"
MOCK="$HUB/edtime/test-mock.json"
mkdir -p "$HUB/edtime"
cat > "$MOCK" <<'JSON'
[{"date": "2026-07-11", "start_time": "08:00", "end_time": "16:30", "shift_code": "SpV", "break_minutes": "30", "status": "planned", "source": "test"}]
JSON

ET="$REPO_DIR/mac/scripts/edtime-process.sh"
EE="$REPO_DIR/mac/scripts/edtime-export-cursor.sh"
if [[ -x "$ET" ]]; then
  bash "$ET" ingest "$MOCK" && ok "edtime-process ingest" || bad "edtime-process ingest"
  bash "$ET" run && ok "edtime-process run" || bad "edtime-process run"
else
  bad "edtime-process not executable"
fi
if [[ -x "$EE" ]]; then
  bash "$EE" "$HUB/edtime/test-export.json" && ok "edtime-export" || bad "edtime-export"
  [[ -f "$HUB/edtime/test-export.json" ]] && ok "export file created" || bad "export file"
else
  bad "edtime-export not executable"
fi

echo ""
echo "▶ Keychain / secrets"
[[ -f "$HUB/secrets.env" ]] && ok "secrets.env exists" || echo "  ⏭️  secrets.env (isi setelah clone)"
security find-generic-password -s automation-hub -a webhook-url -w >/dev/null 2>&1 \
  && ok "webhook Keychain" || echo "  ⏭️  webhook Keychain (set via run-edtime-agentic)"

echo ""
echo "▶ Webhook API"
URL="$(security find-generic-password -s automation-hub -a webhook-url -w 2>/dev/null || true)"
if [[ -n "$URL" ]]; then
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL%%\?*}?action=setup-edtime" 2>/dev/null || echo "000")
  [[ "$CODE" == "200" ]] && ok "setup-edtime HTTP 200" || echo "  ⏭️  setup-edtime HTTP $CODE (redeploy Apps Script)"
else
  echo "  ⏭️  webhook skip"
fi

echo ""
printf "HASIL: %s passed | %s failed\n" "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
