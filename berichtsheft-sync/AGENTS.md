# Vibecoding rules — berichtsheft-sync

Single source of truth for Berichtsheft lives in this folder: `/workspace/berichtsheft-sync` (Mac: often `~/Projects/berichtsheft-sync`).

## Paths

| Path | Role |
|------|------|
| `data/` | Katalog, shifts JSON, attachments (runtime) |
| `docs/` | All guides (`CLOUD_LOCAL_BRIDGE`, `DASHBOARD`, `WHATSAPP`, `TELEGRAM`, `CLOUD_RUN`, …) |
| `scripts/` | Bootstrap, run_local, katalog sync, probes |
| `berichtsheft/` | Python package (API, bots, BLok, sync bridge) |
| `tests/` | Unit / API tests |

Do **not** scatter new Berichtsheft docs outside `berichtsheft-sync/docs/`. Root profile README may only link here.

## Rules

- Mode A default: no BLok/EdTime credentials in repo.
- EdTime: Azubi = import JSON only, no web login adapter until employer provides API/export.
- Never commit `.env`, HAR, screenshots with tokens, `*.db`, or `data/sync_config.json`.
- Activity / Abteilung source of truth: `data/katalog_abteilung.json` (not invent outside this pool).
- After editing the katalog: `python3 -m berichtsheft catalog --reload --write-md`.
- Generator must not invent activities outside the katalog / `templates_hotelfach.json` pool.
- Free days (`frei` / Ausgang): never push to BLok.
- Mac = source of truth for DB/Keychain/bots. Always-on remote: `scripts/start_remote_hub.sh` + `docs/REMOTE_ALWAYS_ON.md`. Cloud ↔ Mac: tunnel + `DASHBOARD_TOKEN`/`BERICHTSHEFT_REMOTE_*` + `/sync/*` — see `docs/CLOUD_LOCAL_BRIDGE.md`. Never expose SQLite without a token.
- WAHA/Docker and Keychain run on Mac only; Cloud VM cannot provide them.
