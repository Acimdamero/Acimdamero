# Berichtsheft-Sync — Otomatisasi Berichtsheft Hotelfachmann Azubi

Sistem **semi-otomatis** untuk mengisi **Berichtsheft** (BLok) bagi Azubi **Hotelfachmann** di Jerman: catatan harian lewat **Telegram (HP)** → orkestrator di **Mac** → isi form **BLok** di web → Anda cek dan setujui dalam **~5 menit** (`/ok`).

> Dibangun untuk alur kerja nyata: jadwal dari EdTime (import JSON), log aktivitas saat shift, terjemahan Indonesia→Jerman, dan worker browser Playwright yang mengisi BLok format **Woche** (Senin–Jumat).

---

## Fitur utama

| Fitur | Deskripsi |
|-------|-----------|
| **Telegram bot** | `/log`, `/selesai`, `/ok`, `/ubah`, `/status`, `/minggu`, `/audit` |
| **Gemini Vision** | Kirim foto (jadwal EdTime, kegiatan, berufsschule) → teks Jerman |
| **Orkestrator** | Gabung log harian + shift + template → draft Berichtsheft |
| **BLok worker** | Dry-run (HTML) dan **live** (Playwright + Keychain) |
| **Audit mingguan** | Scan BLok untuk minggu kosong / draft / lampiran |
| **Keychain macOS** | Password BLok disimpan aman di OS, bukan di git |
| **Cursor SDK** | Perintah `/ai` untuk konsultasi pengembangan (opsional) |

---

## Tech stack (ringkas)

- **Python 3.9+** — inti aplikasi (`berichtsheft/`)
- **FastAPI + Uvicorn** — API lokal untuk bot
- **SQLite** — shifts, work logs, drafts, approvals
- **Playwright** — automasi browser BLok
- **Telegram Bot API** — input dari HP
- **Google Gemini** — polish teks & analisis foto (opsional)
- **Node.js** — `@cursor/sdk` untuk integrasi Cursor (opsional)

Detail lengkap: [docs/TECH_STACK.md](docs/TECH_STACK.md)

---

## Dokumentasi

| File | Isi |
|------|-----|
| [docs/LANDASAN.md](docs/LANDASAN.md) | Latar belakang, masalah, tujuan, ruang lingkup |
| [docs/SETUP.md](docs/SETUP.md) | **Panduan setup urutan lengkap (wajib)** |
| [docs/KATALOG_KEGIATAN.md](docs/KATALOG_KEGIATAN.md) | **Kegiatan per Abteilung — pantau & edit** |
| [docs/TECH_STACK.md](docs/TECH_STACK.md) | Teknologi dan alasan pemilihan |
| [docs/PROSES_PEMBUATAN.md](docs/PROSES_PEMBUATAN.md) | Kronologi pengembangan |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Status implementasi terkini |
| [docs/GITHUB_UPLOAD.md](docs/GITHUB_UPLOAD.md) | Cara upload ke GitHub |
| [docs/PRD.md](docs/PRD.md) | Product requirements |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arsitektur Mac + Keychain |
| [docs/BLok_LIVE.md](docs/BLok_LIVE.md) | Panduan isi BLok live |
| [docs/TELEGRAM.md](docs/TELEGRAM.md) | Setup bot Telegram |
| [docs/GEMINI.md](docs/GEMINI.md) | Setup Gemini API |

---

## Quick start

```bash
cd ~/Projects/berichtsheft-sync
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env          # isi TELEGRAM_BOT_TOKEN, dll.
cp config.example.yaml config.yaml   # sesuaikan selector BLok

python3 -m berichtsheft init
python3 -m berichtsheft import data/shifts_kw23_24.json
python3 -m berichtsheft catalog          # lihat kegiatan per Abteilung
python3 -m berichtsheft test-flow
```

### Edit kegiatan / Abteilung

Sumber kebenaran: [`data/katalog_abteilung.json`](data/katalog_abteilung.json)  
Ringkasan terbaca: [`docs/KATALOG_KEGIATAN.md`](docs/KATALOG_KEGIATAN.md)

```bash
# pantau
python3 -m berichtsheft catalog
python3 -m berichtsheft catalog --abteilung Service
python3 -m berichtsheft catalog --code BRF
python3 -m berichtsheft catalog --db          # isi SQLite runtime

# setelah edit JSON
python3 -m berichtsheft catalog --reload --write-md
```

### Operasi harian

1. Import jadwal EdTime (JSON) — mingguan
2. HP: kirim teks / `/log …` saat kerja
3. HP: `/selesai` → draft + isi BLok (dry-run atau live)
4. HP: `/ok` → setujui
5. Mac harus online (`serve` + `bot` berjalan)

**Kredensial BLok:** Keychain Mac — `python3 -m berichtsheft credentials set --service blok`

---

## Struktur proyek

```
berichtsheft-sync/
├── berichtsheft/       # Modul Python utama
│   ├── catalog.py      # Katalog kegiatan per Abteilung
│   ├── cli.py          # Perintah CLI
│   ├── telegram_bot.py # Bot Telegram
│   ├── api_server.py   # REST API lokal
│   ├── orchestrator.py # Gabung log → draft
│   ├── blok_worker.py  # Playwright BLok
│   └── ...
├── data/
│   ├── katalog_abteilung.json  # ← edit kegiatan di sini
│   ├── areas_hotel.json        # sync otomatis dari katalog
│   ├── templates_hotelfach.json
│   └── blok_mapping.yaml
├── docs/               # Dokumentasi
├── scripts/            # Utilitas (probe, explore, WiFi)
├── tests/              # Unit test
├── config.example.yaml
├── .env.example
└── requirements.txt
```

---

## Keamanan

- **Jangan commit** `.env`, `berichtsheft.db`, `config.yaml` lokal, atau `data/telegram_chat_id.txt`
- Password BLok **hanya** di macOS Keychain
- Token Telegram & API key di `.env` (sudah di `.gitignore`)

---

## Lisensi

Proyek pribadi — gunakan dan modifikasi sesuai kebutuhan Anda sendiri sebagai Azubi.
