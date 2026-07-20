# Proses Pembuatan — Kronologi Pengembangan

Dokumen ini merekonstruksi fase pengembangan **Berichtsheft-Sync** berdasarkan struktur kode, modul, dan dokumentasi yang ada di repositori.

---

## Fase 0 — Fondasi & perencanaan

**Deliverable:** PRD, arsitektur, keputusan desain

| Keputusan | Alasan |
|-----------|--------|
| Mac sebagai stasiun robot | Keychain macOS + browser lokal untuk BLok |
| Telegram sebagai input HP | Cepat saat shift, tidak perlu buka laptop |
| SQLite lokal | Tanpa infrastruktur server |
| EdTime = import JSON manual | Tidak ada API untuk Azubi |

**Artefak:** `docs/PRD.md`, `docs/ARCHITECTURE.md`, `AGENTS.md`

---

## Fase 1 — Database & generator

**Modul:** `db.py`, `seed.py`, `generator.py`, `areas.py`

| Langkah | Output |
|---------|--------|
| Skema SQLite | Tabel shifts, templates, drafts, work_logs, approvals |
| Seed data | Template Hotelfachmann, shift contoh KW23/24 |
| Generator | Draft dari shift + template (deterministik, seeded) |
| Area hotel | `data/areas_hotel.json` → tabel work_areas |

**CLI:** `init`, `import`, `generate`, `preview`, `areas`

**Data contoh:** `data/shifts_kw23_24.json`, `data/templates_hotelfach.json`

---

## Fase 2 — Kredensial & orkestrator

**Modul:** `credentials.py`, `orchestrator.py`, `translate_de.py`

| Langkah | Output |
|---------|--------|
| Keychain integration | `credentials set/test` untuk BLok |
| Orchestrator | Gabung work_logs + shift → draft Jerman |
| Terjemahan ID→DE | Kamus frasa + wrapping kalimat aktivitas |
| Approval flow | Status pending → approved via `/ok` |

**CLI:** `log`, `finish`, `credentials`

**Test:** `tests/test_orchestrator.py`, `tests/test_translate_de.py`

---

## Fase 3 — API & Telegram bot

**Modul:** `api_server.py`, `telegram_bot.py`, `telegram_setup.py`, `config_loader.py`

| Langkah | Output |
|---------|--------|
| FastAPI server | Endpoint log, finish, approve, correct, status |
| Telegram bot | Long-polling, perintah `/log`, `/selesai`, `/ok`, `/ubah` |
| Config loader | `config.yaml` + `.env` dotenv |
| User restriction | `TELEGRAM_ALLOWED_USER_ID` |

**CLI:** `serve`, `bot`, `telegram-init`, `telegram-check`

**Dokumentasi:** `docs/SETUP.md`, `docs/TELEGRAM.md`, `docs/FASE1.md`

---

## Fase 4 — BLok worker (dry-run & live)

**Modul:** `blok_worker.py`, `blok_fields.py`, `blok_hours.py`, `blok_nav.py`, `blok_mapping.py`

| Langkah | Output |
|---------|--------|
| Discovery BLok | Selector Wicket untuk login & form Woche |
| Dry-run | HTML preview di `output/blok_dry_run/` |
| Live fill | Playwright login + isi textarea per hari |
| Format Woche | 1 textarea per hari (Mo=0 … Fr=4) |
| Auto-save | JS `blokUpdateSaveStateSave` per hari |

**CLI:** `worker --date YYYY-MM-DD [--live]`, `finish --fill [--live]`

**Skrip bantu:** `scripts/blok_probe.py`, `scripts/blok_explore_weeks.py`

**Dokumentasi:** `docs/BLok_LIVE.md`, `docs/BLok_WOCHE.md`, `docs/EDTIME_BLok_MAPPING.md`

**Test:** `tests/test_blok_fields.py`, `tests/test_blok_status.py`

---

## Fase 5 — AI: Gemini & Vision

**Modul:** `ai_gemini.py`, `ai_vision.py`

| Langkah | Output |
|---------|--------|
| Gemini polish | Perbaiki tata bahasa draft Jerman |
| Vision analyze | Foto → Stichpunkte / EdTime JSON / berufsschule |
| Mode caption | Deteksi intent dari caption Telegram |
| Integrasi bot | Kirim foto langsung ke `/vision/analyze` |

**CLI:** `gemini-check`, `vision-check`

**Dokumentasi:** `docs/GEMINI.md`

---

## Fase 6 — Audit, lampiran & upload BLok

**Modul:** `blok_audit.py`, `blok_gaps.py`, `blok_upload.py`, `blok_status.py`

| Langkah | Output |
|---------|--------|
| Audit range | Scan minggu di BLok (kosong/draft/isi) |
| Gap detection | Minggu tanpa laporan |
| Attachment DB | Simpan metadata foto dari Vision |
| Upload BLok | Dokumentenablage + einbinden ke hari |
| Reminder | Bot ingatkan otomatis jika ada gap |

**CLI:** `audit`, `minggu`

**Bot:** `/minggu`, `/audit`, `/lampiran`, `/lampirkan`

---

## Fase 7 — Cursor SDK & utilitas

**Modul:** `cursor_agent.py`, `scripts/cursor_prompt.mjs`

| Langkah | Output |
|---------|--------|
| Cursor agent | `/ai` di Telegram untuk dev assist |
| npm dependency | `@cursor/sdk` |

**CLI:** `cursor-check`

---

## Fase 8 — WiFi portal (opsional)

**Modul:** `scripts/wifi_portal.py`

| Langkah | Output |
|---------|--------|
| Deteksi SSID | Cek jaringan kantor |
| Auto-login portal | Klik tombol captive portal |

**Status:** Opsional, butuh konfigurasi `wifi.*` di `config.yaml`

**Dokumentasi:** `docs/WIFI.md`

---

## Fase 9 — Pengujian & dokumentasi

| Artefak | Isi |
|---------|-----|
| `docs/LAPORAN_UJI_COBA.md` | Hasil uji 2026-06-03 |
| `docs/PROGRESS.md` | Checklist status |
| `tests/` | Unit test orchestrator, translate, blok |
| `test-flow` CLI | Simulasi end-to-end tanpa Telegram |

---

## Timeline perkiraan (berdasarkan artefak)

| Periode | Fase |
|---------|------|
| Awal Juni 2026 | Fase 0–1: PRD, DB, generator |
| 3 Juni 2026 | Fase 2–4: orchestrator, API, dry-run (uji coba v0.2) |
| 4–5 Juni 2026 | Fase 4–6: live worker, selector Woche, audit, Vision |
| 5 Juni 2026 | Fase 9: dokumentasi GitHub, persiapan upload |

---

## Status saat ini

Lihat [PROGRESS.md](PROGRESS.md) untuk checklist terkini.

**Inti sudah berjalan:** DB, orchestrator, Telegram, dry-run & live worker, Gemini Vision, audit mingguan.

**Opsional / perlu penyesuaian:** WiFi portal, submit otomatis L2 penuh, selector BLok jika UI berubah.
