# Cloud ↔ Mac bridge — Berichtsheft

Goal: edit/input from **Cursor Cloud** while the **authoritative SQLite DB**, **macOS Keychain**, and **WAHA/Docker** stay on your **Mac**.

Do **not** expose `berichtsheft.db` as an open file share. Always use the HTTP API with `DASHBOARD_TOKEN` or `SYNC_TOKEN`.

---

## Architecture (recommended MVP — Option A)

```
[Phone Telegram/WhatsApp]          [Cursor Cloud / dashboard]
         │                                    │
         │                         BERICHTSHEFT_API /
         │                         remote_api_url
         ▼                                    │
[MacBook] ◄──── Cloudflare Tunnel / Tailscale ◘
  • python3 -m berichtsheft serve  (:8765)
  • SQLite berichtsheft.db
  • Keychain (BLok)
  • WAHA Docker (:3000)
  • Telegram / WhatsApp bots
```

| Role | What lives there |
|------|------------------|
| **Mac** | DB, Keychain, WAHA, Playwright BLok, bots |
| **Cloud VM** | Code edit, katalog JSON via git, optional dashboard pointing at Mac tunnel |
| **GitHub** | Katalog / docs / code — not runtime secrets or `.db` |

### Mac setup

```bash
cd ~/Projects/berichtsheft-sync   # or /workspace/berichtsheft-sync on Cloud
# .env: DASHBOARD_TOKEN=… (or SYNC_TOKEN=…)  — never commit
# config.yaml: server.host: "0.0.0.0"  if binding for tunnel

python3 -m berichtsheft serve
# separate terminal / tmux:
cloudflared tunnel --url http://127.0.0.1:8765
# or Tailscale Serve / Funnel to :8765
```

Open dashboard from anywhere:

```text
https://<tunnel-host>/dashboard?token=<DASHBOARD_TOKEN>
```

Point Cloud agents / bots at the same host:

```bash
# on Cloud .env (no secrets in git)
BERICHTSHEFT_API=https://<tunnel-host>
BERICHTSHEFT_REMOTE_API=https://<tunnel-host>
DASHBOARD_TOKEN=<same-as-mac>
# optional dedicated sync token:
# SYNC_TOKEN=<same-or-separate>
```

Cloud then uses Mac DB for `/log`, `/finish`, dashboard editors, etc., without copying SQLite.

---

## Option B — snapshot sync (push/pull)

When both sides run a local API (or offline batches), exchange JSON snapshots:

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /sync/status` | Bearer / `X-Sync-Token` / `X-Dashboard-Token` | Counts + remote URL config |
| `GET /sync/pull` | same | Export shifts, work_logs, drafts, approvals, katalog JSON, attachment meta |
| `POST /sync/push` | same | Import payload (`mode=merge` or `replace`) |

### CLI

```bash
# On Cloud: pull latest from Mac tunnel into Cloud scratch DB
python3 -m berichtsheft sync-pull --url https://<tunnel-host>

# On Mac: pull edits that Cloud pushed (if Cloud exposed a tunnel too)
python3 -m berichtsheft sync-pull --url https://<cloud-tunnel>

# Push local snapshot to remote
python3 -m berichtsheft sync-push --url https://<tunnel-host> --mode merge

python3 -m berichtsheft sync-status
```

Token resolution: `--token` → `SYNC_TOKEN` → `DASHBOARD_TOKEN`.

Optional: `--files` includes small attachment binaries as base64 (cap ~2 MiB each).

### Dashboard panel

Ops console → **Cloud ↔ Mac**:

- Shows local counts, last pull/push, last error
- Saves `data/sync_config.json` → `remote_api_url`
- Buttons: Pull from remote / Push to remote

---

## What Cloud can vs cannot do

| Works on Cloud | Needs Mac |
|----------------|-----------|
| API `/health`, `/dashboard` (local scratch DB) | Live BLok (Playwright + Keychain) |
| Katalog edit + git | WAHA / WhatsApp personal |
| Sync pull/push to Mac API | Docker WAHA |
| Telegram bot *if* token in `.env` and polling here | Production DB of record |

See also: [CLOUD_RUN.md](CLOUD_RUN.md), [DASHBOARD.md](DASHBOARD.md), [DUA_KOMPUTER.md](DUA_KOMPUTER.md), [WHATSAPP.md](WHATSAPP.md).

---

## Security checklist

- [ ] `DASHBOARD_TOKEN` or `SYNC_TOKEN` set on any publicly tunneled host
- [ ] Never commit `.env`, `*.db`, tokens, or Keychain exports
- [ ] Prefer Cloudflare Tunnel / Tailscale over raw port-forward to the internet
- [ ] Do not mount or rsync `berichtsheft.db` without encryption + access control
- [ ] Rotate token if a tunnel URL was shared in chat logs
