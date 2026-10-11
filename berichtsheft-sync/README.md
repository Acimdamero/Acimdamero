# Berichtsheft-Sync — Otomatisasi Berichtsheft Hotelfachmann Azubi

Sistem **semi-otomatis** untuk mengisi **Berichtsheft** (BLok) bagi Azubi **Hotelfachmann** di Jerman: catatan harian lewat **Telegram** atau **WhatsApp (HP)** → orkestrator di **Mac** → isi form **BLok** di web → Anda cek dan setujui dalam **~5 menit** (`/ok`).

> Dibangun untuk alur kerja nyata: jadwal dari EdTime (import JSON), log aktivitas saat shift, terjemahan Indonesia→Jerman, dan worker browser Playwright yang mengisi BLok format **Woche** (Senin–Jumat).

---

## Fitur utama

| Fitur | Deskripsi |
|-------|-----------|
| **Telegram bot** | `/log`, `/selesai`, `/ok`, `/ubah`, `/status`, `/minggu`, `/audit` |
| **WhatsApp bot** | Nomor personal via WAHA — menu bernomor + perintah sama seperti Telegram |
| **Ops dashboard** | Monitoring + edit katalog/jadwal di browser — [docs/DASHBOARD.md](docs/DASHBOARD.md) |
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
- **WAHA** — WhatsApp personal (self-host, sama stack Automation Hub)
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
| [docs/DUA_KOMPUTER.md](docs/DUA_KOMPUTER.md) | **PC kantor + MacBook tanpa ganggu jaringan admin** |
| [docs/TECH_STACK.md](docs/TECH_STACK.md) | Teknologi dan alasan pemilihan |
| [docs/PROSES_PEMBUATAN.md](docs/PROSES_PEMBUATAN.md) | Kronologi pengembangan |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Status implementasi terkini |
| [docs/GITHUB_UPLOAD.md](docs/GITHUB_UPLOAD.md) | Cara upload ke GitHub |
| [docs/PRD.md](docs/PRD.md) | Product requirements |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arsitektur Mac + Keychain |
| [docs/BLok_LIVE.md](docs/BLok_LIVE.md) | Panduan isi BLok live |
| [docs/TELEGRAM.md](docs/TELEGRAM.md) | Setup bot Telegram |
| [docs/WHATSAPP.md](docs/WHATSAPP.md) | **Setup bot WhatsApp (WAHA + nomor personal)** |
| [docs/DASHBOARD.md](docs/DASHBOARD.md) | **Ops dashboard — monitor + edit katalog/jadwal** |
| [docs/CLOUD_LOCAL_BRIDGE.md](docs/CLOUD_LOCAL_BRIDGE.md) | **Cloud ↔ Mac DB** (tunnel + `/sync` push/pull) |
| [docs/CLOUD_RUN.md](docs/CLOUD_RUN.md) | Cursor Cloud VM paths & bootstrap |
| [docs/GEMINI.md](docs/GEMINI.md) | Setup Gemini API |

---

## Quick start

```bash
# Mac:
cd ~/Projects/berichtsheft-sync
# Cursor Cloud VM:
# cd /workspace/berichtsheft-sync

python3 -m venv .venv && source .venv/bin/activate   # optional; Cloud often uses system pip --user
pip install -r requirements.txt
playwright install chromium

cp .env.example .env          # isi TELEGRAM_BOT_TOKEN, DASHBOARD_TOKEN, dll.
cp config.example.yaml config.yaml   # sesuaikan selector BLok

python3 -m berichtsheft init
python3 -m berichtsheft import data/shifts_kw23_24.json
python3 -m berichtsheft catalog          # lihat kegiatan per Abteilung
python3 -m berichtsheft test-flow
# Cloud one-shot: bash scripts/bootstrap_and_run.sh
```

### Cloud ↔ Mac sync

```bash
# Mac: serve + tunnel (DASHBOARD_TOKEN wajib)
python3 -m berichtsheft serve
cloudflared tunnel --url http://127.0.0.1:8765

# Cloud: point at Mac
python3 -m berichtsheft sync-pull --url https://<tunnel-host>
python3 -m berichtsheft sync-push --url https://<tunnel-host>
```

Detail: [docs/CLOUD_LOCAL_BRIDGE.md](docs/CLOUD_LOCAL_BRIDGE.md)

### Edit kegiatan / Abteilung

Sumber kebenaran: [`data/katalog_abteilung.json`](data/katalog_abteilung.json)  
Ringkasan terbaca: [`docs/KATALOG_KEGIATAN.md`](docs/KATALOG_KEGIATAN.md)

**PC kantor (Cursor) vs MacBook:** lihat [`docs/DUA_KOMPUTER.md`](docs/DUA_KOMPUTER.md) — edit katalog di kantor lewat GitHub; DB/bot/BLok tetap hanya di Mac. Tidak perlu VPN atau sambung ke laptop.

```bash
# pantau (boleh di mana saja)
python3 -m berichtsheft catalog
python3 -m berichtsheft catalog --abteilung Service
python3 -m berichtsheft catalog --code BRF

# di MacBook setelah git pull dari edit kantor:
./scripts/sync_katalog_from_git.sh
# atau: python3 -m berichtsheft catalog --reload --write-md
```

### Ops dashboard

```bash
python3 -m berichtsheft serve          # atau: python3 -m berichtsheft dashboard
# lokal: http://127.0.0.1:8765/dashboard
# HP / remote: set DASHBOARD_TOKEN + tunnel — lihat docs/DASHBOARD.md
```

Edit katalog / jadwal dari UI — lihat [docs/DASHBOARD.md](docs/DASHBOARD.md).

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
berichtsheft-sync/          # ← single source of truth
├── berichtsheft/           # Modul Python utama
│   ├── sync_bridge.py      # Cloud ↔ Mac /sync push-pull
│   ├── api_server.py       # REST API (+ /sync + webhook WA)
│   ├── dashboard.py        # Ops dashboard /dashboard
│   ├── catalog.py / cli.py / telegram_bot.py / whatsapp_bot.py …
├── data/                   # katalog, shifts, attachments
├── docs/                   # ALL guides (CLOUD_LOCAL_BRIDGE, DASHBOARD, …)
├── scripts/                # bootstrap_and_run, run_local, probes
├── tests/
├── config.example.yaml
├── .env.example
└── requirements.txt
```

---

## Keamanan

- **Jangan commit** `.env`, `berichtsheft.db`, `config.yaml` lokal, `data/telegram_chat_id.txt`, atau `data/whatsapp_*.txt` / `whatsapp_seen_ids.json`
- Password BLok **hanya** di macOS Keychain
- Token Telegram, WAHA key & API key di `.env` (sudah di `.gitignore`)

---

## Lisensi

Proyek pribadi — gunakan dan modifikasi sesuai kebutuhan Anda sendiri sebagai Azubi.
