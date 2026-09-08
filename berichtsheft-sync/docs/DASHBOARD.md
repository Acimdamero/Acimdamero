# Dashboard ops — Berichtsheft-Sync

Internal monitoring + editing console for API, bots, katalog, jadwal, and BLok dry-run output.

## Open

```bash
cd berichtsheft-sync
export PYTHONPATH=.
# optional: set DASHBOARD_TOKEN=... in .env
python3 -m berichtsheft serve
# or: python3 -m berichtsheft dashboard
```

Then open:

- **Dashboard:** http://127.0.0.1:8765/dashboard
- **Health JSON:** http://127.0.0.1:8765/dashboard/api/health
- **API health:** http://127.0.0.1:8765/health

If `DASHBOARD_TOKEN` is set in `.env`, send header `X-Dashboard-Token: <token>` (or paste it in the sidebar Token field). If empty, the dashboard allows access — use only on localhost / private network.

## Panels

| Panel | Apa yang ditampilkan / diedit |
|-------|-------------------------------|
| **Overview** | Health: API, Gemini, Vision, Cursor, Telegram token, WA allowlist, WAHA reachability |
| **Live feed** | Recent `work_logs`, drafts, attachments (+ thumbnail jika file ada di `data/attachments/`) |
| **Katalog / Abteilung** | Editor JSON untuk `data/katalog_abteilung.json` → Save menulis file + `catalog.sync_to_db` + export legacy |
| **Jadwal / Shifts** | Tabel SQLite shifts (upsert/delete) + editor sample `data/shifts_kw23_24.json` (save + import DB) |
| **Sekolah / Templates** | Baca Abteilung Schule dari katalog + template texts |
| **BLok dry-run** | Status offline/dry-run; iframe HTML / JSON dari `output/blok_dry_run/` (tidak login live BLok di cloud) |
| **Bots** | Telegram/WhatsApp: chat id tersimpan?, daftar perintah, link docs |

## Edit katalog dari UI

1. Sidebar → **Katalog / Abteilung**
2. Edit JSON (struktur `abteilungen` → `codes` → `templates_de`, dll.)
3. Klik **Save + Sync DB**
4. File `data/katalog_abteilung.json` ter-update; SQLite `activity_templates` / `work_areas` di-reload; `areas_hotel.json` + `templates_hotelfach.json` ikut di-sync

Setara CLI:

```bash
python3 -m berichtsheft catalog --reload --write-md
```

## Edit jadwal dari UI

1. **Jadwal / Shifts** → tab **SQLite shifts**: isi form Upsert (date, type, jam, tags) → **Upsert**
2. Atau tab **Sample JSON**: edit `shifts_kw23_24.json` → **Save + Import DB**

## API endpoints (ringkas)

Semua di bawah `/dashboard/api/…` (auth sama seperti di atas):

- `GET /dashboard/api/health`
- `GET /dashboard/api/live`
- `GET|PUT /dashboard/api/catalog`
- `GET|PUT /dashboard/api/shifts` · `DELETE /dashboard/api/shifts/{date}`
- `GET|PUT /dashboard/api/shifts/json`
- `GET /dashboard/api/school`
- `GET /dashboard/api/blok`
- `GET /dashboard/api/bots`

## Keamanan

- Jangan commit `.env`, token, Gemini keys, atau `berichtsheft.db`
- Live BLok credentials tetap di macOS Keychain — dashboard cloud hanya menampilkan dry-run
- Produksi: isi `DASHBOARD_TOKEN` dan jangan expose port ke internet publik
