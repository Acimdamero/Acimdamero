#!/bin/bash
# Simpan referensi akun edtime di Apple Keychain (Mac) — BUKAN password di Sheet/git.
# Password sebenarnya disimpan di iPhone Keychain / 1Password; Mac hanya metadata + webhook.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=edtime-lib.sh
source "$SCRIPT_DIR/edtime-lib.sh"

usage() {
  cat <<'EOF'
edtime-save-credentials.sh — simpan konfigurasi edtime ke Keychain Mac

Usage:
  edtime-save-credentials.sh webhook <APPS_SCRIPT_WEB_APP_URL>
  edtime-save-credentials.sh edtime-user <email_or_username>
  edtime-save-credentials.sh edtime-note <catatan employer/url login>
  edtime-save-credentials.sh show

Catatan keamanan:
  - JANGAN simpan password edtime di config.env atau Google Sheet
  - Login di iPhone: edtime app ingat session setelah login manual pertama
  - iPhone Shortcut pakai Passwords action (iOS 18+) jika perlu assist login
EOF
}

SERVICE="${KEYCHAIN_SERVICE:-edtime-sync}"

save_secret() {
  local account="$1"
  local value="$2"
  security delete-generic-password -s "$SERVICE" -a "$account" 2>/dev/null || true
  security add-generic-password -s "$SERVICE" -a "$account" -w "$value"
  edtime_log "INFO" "Keychain disimpan: $account"
}

show_secrets() {
  echo "=== edtime Keychain ($SERVICE) ==="
  for acct in webhook-url edtime-user edtime-note; do
    val="$(get_keychain_secret "$acct" 2>/dev/null || echo "(not set)")"
    if [[ "$acct" == "webhook-url" && "$val" != "(not set)" ]]; then
      val="${val:0:40}..."
    fi
    echo "  $acct: $val"
  done
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  webhook)
    URL="${1:?Web App URL required}"
    save_secret "webhook-url" "$URL"
    ;;
  edtime-user)
    USER="${1:?Username/email required}"
    save_secret "edtime-user" "$USER"
    ;;
  edtime-note)
    NOTE="${1:?Note required}"
    save_secret "edtime-note" "$NOTE"
    ;;
  show)
    show_secrets
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac
