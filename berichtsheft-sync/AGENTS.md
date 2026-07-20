# Vibecoding rules — berichtsheft-sync

- Mode A default: no BLok/EdTime credentials in repo.
- EdTime: Azubi = import JSON only, no web login adapter until employer provides API/export.
- Never commit `.env`, HAR, screenshots with tokens.
- Activity / Abteilung source of truth: `data/katalog_abteilung.json` (not invent outside this pool).
- After editing the katalog: `python3 -m berichtsheft catalog --reload --write-md`.
- Generator must not invent activities outside the katalog / `templates_hotelfach.json` pool.
- Free days (`frei` / Ausgang): never push to BLok.
