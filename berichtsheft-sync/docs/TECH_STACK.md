# Tech Stack — Berichtsheft-Sync

Dokumen ini menjelaskan teknologi yang dipakai dan **mengapa** dipilih, berdasarkan kode aktual di repositori.

---

## Ringkasan

| Lapisan | Teknologi | Versi minimum |
|---------|-----------|---------------|
| Bahasa utama | Python | 3.9+ |
| API lokal | FastAPI + Uvicorn | 0.110 / 0.29 |
| HTTP client | httpx | 0.27 |
| Database | SQLite (stdlib) | — |
| Browser automation | Playwright | 1.42 |
| Config | YAML (PyYAML) | 6.0 |
| Bot | Telegram Bot API (httpx) | — |
| AI teks & vision | Google Gemini API | gemini-2.5-flash |
| AI dev assistant | Cursor SDK (@cursor/sdk) | 1.0 |
| Runtime Node | Node.js | untuk Cursor SDK |

---

## Python — inti aplikasi

**Paket:** `berichtsheft/` (28 modul)

Semua logika bisnis ditulis dalam Python karena:

- Ekosistem matang untuk scripting, SQLite, dan CLI
- Playwright Python stabil untuk automasi BLok
- Mudah dijalankan di Mac tanpa infrastruktur cloud

### Modul utama

| Modul | Fungsi |
|-------|--------|
| `cli.py` | Entry point: `python3 -m berichtsheft <perintah>` |
| `db.py` | Skema SQLite: shifts, work_logs, drafts, approvals, attachments |
| `orchestrator.py` | Gabung log + shift → draft Jerman |
| `generator.py` | Template-based draft dari `templates_hotelfach.json` |
| `translate_de.py` | Kamus ID→DE + wrapping kalimat aktivitas |
| `api_server.py` | REST API FastAPI untuk bot & integrasi |
| `telegram_bot.py` | Long-polling bot Telegram |
| `blok_worker.py` | Playwright: login, isi form Woche, simpan |
| `blok_audit.py` | Scan status minggu di BLok |
| `blok_upload.py` | Upload foto ke Dokumentenablage |
| `credentials.py` | macOS Keychain via `security` CLI |
| `ai_gemini.py` | Polish teks Jerman |
| `ai_vision.py` | Analisis foto (EdTime, kegiatan, sekolah) |
| `cursor_agent.py` | Wrapper Cursor SDK untuk `/ai` |

---

## FastAPI + Uvicorn

**Mengapa:** API ringan yang menghubungkan bot Telegram (proses terpisah) dengan database dan worker.

**Endpoint utama** (`api_server.py`):

- `GET /health` — status gemini/vision/cursor
- `POST /log`, `/finish`, `/approve`, `/correct`
- `POST /vision/analyze` — foto → teks
- `POST /ai` — Cursor agent
- `GET /audit/weeks` — scan gap mingguan
- `POST /attachments/upload-blok` — lampiran ke BLok

Bot memanggil `http://127.0.0.1:8765` (konfigurasi `BERICHTSHEFT_API` di `.env`).

---

## SQLite

**Mengapa:** Data lokal per-Azubi, tanpa server DB terpisah. File `berichtsheft.db` di root proyek (di-gitignore).

**Tabel:**

- `shifts` — jadwal import EdTime
- `work_logs` — catatan harian dari Telegram/CLI
- `draft_entries` — draft Berichtsheft yang dihasilkan
- `approvals` — status `/ok`
- `activity_templates` — template kegiatan Hotelfachmann
- `work_areas` — zona hotel (BRF, HK, Tagung, …)
- `attachments` — metadata foto untuk upload BLok

---

## Playwright

**Mengapa:** BLok adalah aplikasi web Wicket tanpa API publik. Satu-satunya cara otomasi yang andal adalah browser sungguhan.

**Penggunaan:**

- `blok_worker.py` — login + isi textarea per hari (format Woche)
- `blok_audit.py` — baca status minggu (readonly + editable)
- `blok_upload.py` — upload file ke Dokumentenablage
- `scripts/blok_probe.py`, `blok_explore_weeks.py` — discovery selector

**Instalasi browser:**

```bash
playwright install chromium
```

---

## Telegram Bot API

**Mengapa:** Input dari HP saat kerja — lebih cepat daripada buka laptop.

**Implementasi:** Long-polling langsung via `httpx` (tanpa library python-telegram-bot) untuk mengurangi dependensi.

**Token:** `TELEGRAM_BOT_TOKEN` di `.env` (bukan di kode).

---

## Google Gemini

**Mengapa:** Polish teks Jerman natural + analisis foto (screenshot EdTime, dokumentasi kegiatan).

**Modul:** `ai_gemini.py`, `ai_vision.py`

**Konfigurasi `.env`:**

```
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
AI_POLISH_ENABLED=true
AI_VISION_ENABLED=true
```

Opsional — sistem tetap jalan dengan kamus `translate_de.py` jika API key kosong.

---

## Cursor SDK

**Mengapa:** Perintah `/ai` di Telegram untuk konsultasi teknis saat pengembangan (bukan runtime harian Berichtsheft).

**Paket:** `@cursor/sdk` (Node.js) dipanggil dari `cursor_agent.py` via subprocess.

---

## macOS Keychain

**Mengapa:** Password BLok tidak boleh di `.env`, git, atau prompt AI.

**Implementasi:** `credentials.py` memanggil utilitas `security` bawaan macOS.

```bash
python3 -m berichtsheft credentials set --service blok
python3 -m berichtsheft credentials test --service blok
```

---

## YAML configuration

**File:** `config.example.yaml` → salin ke `config.yaml` (di-gitignore)

Berisi:

- URL dan selector CSS BLok (Wicket)
- Flag orchestrator (`live_blok_after_finish`, dll.)
- Pengaturan reminder Telegram
- Konfigurasi WiFi portal (opsional)

---

## Node.js (opsional)

Hanya untuk `@cursor/sdk`. Tidak diperlukan untuk operasi harian Berichtsheft.

```bash
npm install   # sekali
```

---

## Testing

| Framework | Cakupan |
|-----------|---------|
| `unittest` (stdlib) | orchestrator, translate_de, blok_fields, blok_status |

```bash
python3 -m unittest discover -s tests -v
```

---

## Dependensi lengkap

**Python** (`requirements.txt`):

```
httpx>=0.27.0
fastapi>=0.110.0
uvicorn>=0.29.0
pyyaml>=6.0
playwright>=1.42.0
```

**Node.js** (`package.json`):

```json
{ "dependencies": { "@cursor/sdk": "^1.0.18" } }
```

---

## Diagram alur data

```
[Telegram HP] ──HTTP──► [FastAPI :8765]
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
               [SQLite]  [Orchestrator] [Gemini]
                    │         │
                    └────┬────┘
                         ▼
                  [Playwright Worker]
                         │
                         ▼
                    [BLok Web]
```
