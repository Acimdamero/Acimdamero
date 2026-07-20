# Laporan uji coba — Berichtsheft-Sync v0.2

**Tanggal uji:** 2026-06-03  
**Lingkungan:** macOS, Python 3.9, path `~/Projects/berichtsheft-sync`

## Hasil otomatis

| Uji | Perintah | Hasil |
|-----|----------|--------|
| Init DB + seed | `python3 -m berichtsheft init` | ✓ 17 template, 12 shift, 4 area |
| Alur simulasi | `python3 -m berichtsheft test-flow` | ✓ Draft + `output/blok_dry_run/2026-06-04.html` |
| Unit test | `python3 -m unittest tests.test_orchestrator` | ✓ 3/3 passed (setelah fix terjemahan) |

## Belum diuji (butuh Anda)

| Uji | Prasyarat |
|-----|-----------|
| Keychain BLok | `credentials set` di Terminal Mac |
| Telegram bot | `TELEGRAM_BOT_TOKEN` di `.env` + `serve` + `bot` |
| BLok live | `config.yaml` selector disesuaikan + `worker --live` |
| WiFi portal | `wifi.*` di `config.yaml` + SSID kantor |

## Artefak contoh

- `output/blok_dry_run/2026-06-04.html` — preview isi yang akan dikirim ke BLok
- `output/blok_dry_run/2026-06-04.json` — payload mesin

## Kesimpulan

Fase 1–4 (DB, orchestrator, dry-run worker, API+bot code) **siap**.  
Fase 5–6 (Telegram production, BLok live) menunggu **token Telegram** + **kredensial Keychain** + **penyesuaian selector BLok** oleh Anda.
