#!/bin/bash
# Test semua fitur Automation Hub — jalankan di Mac setelah WAHA WORKING.
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB="${AUTOMATION_HUB_HOME:-$HOME/.automation-hub}/run-task.sh"
CONTACT="${TEST_CONTACT_NAME:-agwen acim damero jerman}"
PASS=0
FAIL=0
SKIP=0

ok()  { echo "  ✅ $1"; PASS=$((PASS+1)); }
bad() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }
skip(){ echo "  ⏭️  $1"; SKIP=$((SKIP+1)); }

run_ok() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then ok "$name"; else bad "$name"; fi
}

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     AUTOMATION HUB — FULL FEATURE TEST                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Install ─────────────────────────────────────────────────
echo "▶ [1/8] Install & files"
[[ -x "$HUB" ]] && ok "run-task.sh executable" || bad "run-task.sh missing"
[[ -f "$HOME/.automation-hub/config.env" ]] && ok "config.env" || skip "config.env (optional)"

# ── 2. Docker ──────────────────────────────────────────────────
echo ""
echo "▶ [2/8] Docker & WAHA"
if docker info >/dev/null 2>&1; then
  ok "docker info"
else
  bad "docker info — buka Docker Desktop"
fi

if docker ps --format '{{.Names}}' 2>/dev/null | grep -q automation-hub-waha; then
  ok "WAHA container running"
else
  bad "WAHA container — jalankan: docker compose up -d"
fi

HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/ 2>/dev/null || echo "000")
[[ "$HTTP" =~ ^(200|401|302)$ ]] && ok "localhost:3000 (HTTP $HTTP)" || bad "localhost:3000 unreachable"

# ── 3. WAHA session ────────────────────────────────────────────
echo ""
echo "▶ [3/8] WhatsApp session"
SESSION_JSON=$(curl -sf http://127.0.0.1:3000/api/sessions/default \
  -H "X-Api-Key: ${WAHA_API_KEY:-automation-hub-test-key}" 2>/dev/null || echo '{}')
if echo "$SESSION_JSON" | grep -q '"status":"WORKING"'; then
  ok "WhatsApp session WORKING"
else
  bad "WhatsApp not WORKING — scan QR di dashboard"
  echo "       $(echo "$SESSION_JSON" | head -c 120)"
fi

# ── 4. Hub commands ────────────────────────────────────────────
echo ""
echo "▶ [4/8] Hub commands"
run_ok "help" "$HUB" help
run_ok "status" "$HUB" status
run_ok "waha-status" "$HUB" waha-status

# ── 5. Kirim WA ──────────────────────────────────────────────────
echo ""
echo "▶ [5/8] Kirim WhatsApp"
if echo "$SESSION_JSON" | grep -q '"status":"WORKING"'; then
  TS=$(date +%H:%M:%S)
  if "$HUB" waha-send-name "$CONTACT" "🧪 Test Hub [$TS] — kirim otomatis OK"; then
    ok "waha-send-name → $CONTACT"
  else
    bad "waha-send-name gagal"
  fi
else
  skip "waha-send (session not WORKING)"
fi

# ── 6. Auto-reply webhook ──────────────────────────────────────
echo ""
echo "▶ [6/8] Auto-reply (inbound chat)"
RELAY="$REPO_DIR/mac/scripts/waha-auto-reply.sh"
if [[ -x "$RELAY" ]]; then
  if bash "$RELAY" start 2>/dev/null; then
    ok "webhook relay + WAHA webhook configured"
    echo "       → Kirim pesan 'test' ke nomor WA Anda dari HP lain untuk uji balasan"
  else
    bad "auto-reply start gagal"
  fi
else
  skip "waha-auto-reply.sh not found"
fi

# ── 7. Mac control (non-destructive) ─────────────────────────────
echo ""
echo "▶ [7/8] Mac control (safe tests)"
if [[ "$(uname -s)" == "Darwin" ]]; then
  run_ok "open-app Calculator" "$HUB" open-app Calculator
  sleep 1
  run_ok "quit-app Calculator" "$HUB" quit-app Calculator
  skip "sleep/wake (skipped — tidak ditest otomatis)"
else
  skip "Mac app control (bukan macOS)"
fi

# ── 8. Optional integrations ───────────────────────────────────
echo ""
echo "▶ [8/8] Integrasi opsional"
[[ -n "${GOOGLE_SHEET_ID:-}" && "${GOOGLE_SHEET_ID}" != "your_google_sheet_id_here" ]] \
  && ok "GOOGLE_SHEET_ID configured" || skip "Google Sheet (belum di-set)"
[[ -f "$HOME/.ssh/automation_hub.pub" ]] && ok "SSH key iPhone" || skip "SSH key"
command -v op >/dev/null && ok "1Password CLI" || skip "1Password CLI"

# ── Summary ──────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
printf "║  HASIL: %-3s passed | %-3s failed | %-3s skipped        ║\n" "$PASS" "$FAIL" "$SKIP"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
if [[ "$FAIL" -eq 0 ]]; then
  echo "✅ Semua test inti LULUS"
  echo ""
  echo "Test chat balasan manual:"
  echo "  1. Dari HP lain, kirim WA ke nomor Anda: 'test'"
  echo "  2. Harus dapat balasan otomatis dalam ~5 detik"
  echo "  3. Cek log: tail -f ~/.automation-hub/logs/waha-inbox.log"
  exit 0
else
  echo "⚠️  Ada $FAIL test gagal — perbaiki item ❌ di atas"
  exit 1
fi
