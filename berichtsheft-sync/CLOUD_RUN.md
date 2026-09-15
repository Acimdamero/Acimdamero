# Cloud Agent VM — run commands

Use these paths only. Do **not** use `~/Projects/...` on this VM.

## Layout

- Repo root: `/workspace`
- App: `/workspace/berichtsheft-sync`
- Branch with dashboard + bots: `cursor/berichtsheft-dashboard-5f8c`

## One-shot start

```bash
cd /workspace
git fetch origin cursor/berichtsheft-dashboard-5f8c
git checkout cursor/berichtsheft-dashboard-5f8c

cd /workspace/berichtsheft-sync
pip3 install --user -r requirements.txt
# Prefer system python + pip --user. Do not rely on venv/ensurepip in this VM.

bash scripts/bootstrap_and_run.sh
```

This starts:

- `tmux` session `bericht-api` → `PYTHONPATH=/workspace/berichtsheft-sync python3 -m berichtsheft serve` on `0.0.0.0:8765`
- `tmux` session `bericht-bot` → Telegram bot (`python3 -m berichtsheft bot`)
- Ensures `DASHBOARD_TOKEN` exists in `.env` (random if missing; never commit)

## Akses dari HP / mana saja

Dashboard bind ke `0.0.0.0:8765` supaya bisa di-tunnel. **Jangan** buka tanpa `DASHBOARD_TOKEN`.

```bash
# Token (redact mid-string jika log panjang)
grep '^DASHBOARD_TOKEN=' /workspace/berichtsheft-sync/.env

# Quick tunnel (prefer cloudflared)
cloudflared tunnel --url http://127.0.0.1:8765
# fallback: npx localtunnel --port 8765
```

Di browser HP:

```text
https://<tunnel-host>/dashboard?token=<DASHBOARD_TOKEN>
```

Alternatif: Cursor **Ports** → forward `8765`, atau deploy (Railway/Fly/VPS) dengan env `DASHBOARD_TOKEN` + HTTPS.

Auth: `?token=`, `Authorization: Bearer`, `X-Dashboard-Token`, atau cookie `bh_dashboard_token`. Detail: [docs/DASHBOARD.md](docs/DASHBOARD.md).

## Manual start (if bootstrap is unavailable)

```bash
cd /workspace/berichtsheft-sync
export PYTHONPATH=/workspace/berichtsheft-sync

# stop old sessions by name only
tmux -f /exec-daemon/tmux.portal.conf kill-session -t bericht-api 2>/dev/null || true
tmux -f /exec-daemon/tmux.portal.conf kill-session -t bericht-bot 2>/dev/null || true

tmux -f /exec-daemon/tmux.portal.conf new-session -d -s bericht-api -c /workspace/berichtsheft-sync -- \
  bash -lc 'export PYTHONPATH=/workspace/berichtsheft-sync; python3 -m berichtsheft serve 2>&1 | tee logs/api.log'

tmux -f /exec-daemon/tmux.portal.conf new-session -d -s bericht-bot -c /workspace/berichtsheft-sync -- \
  bash -lc 'export PYTHONPATH=/workspace/berichtsheft-sync; set -a; source .env; set +a; python3 -m berichtsheft bot 2>&1 | tee logs/bot.log'
```

Without `PYTHONPATH=/workspace/berichtsheft-sync` you get `No module named berichtsheft`.

## Verify

```bash
curl -sS http://127.0.0.1:8765/health
# without token → 401 when DASHBOARD_TOKEN set
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/dashboard
TOKEN=$(grep '^DASHBOARD_TOKEN=' /workspace/berichtsheft-sync/.env | cut -d= -f2-)
curl -sS -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8765/dashboard?token=$TOKEN"
cd /workspace/berichtsheft-sync
PYTHONPATH=/workspace/berichtsheft-sync python3 -m berichtsheft telegram-check
tmux -f /exec-daemon/tmux.portal.conf ls
```

Expect: health JSON with `"ok":true` (and `"gemini":true` if `GEMINI_API_KEY` is set), dashboard HTTP `401` without token / `200` with `?token=`, telegram-check OK, sessions `bericht-api` + `bericht-bot`.

## Env

Keep secrets in `/workspace/berichtsheft-sync/.env` (never commit). Preserve existing `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `WHATSAPP_ALLOWED_NUMBER`, and `DASHBOARD_TOKEN`.

## WAHA / WhatsApp

Docker is **not** installed on this Cloud Agent VM. WAHA and live WhatsApp stay **Mac-only**. Do not try `docker compose` or `~/Projects/mac-iphone-automation` here.
