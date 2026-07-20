# Fase 1 — API, Telegram, Vision, Cursor

Fase 1 menghubungkan log kerja harian (Telegram) ke draft Berichtsheft di Mac, dengan opsi AI.

## Prasyarat

```bash
cd ~/Projects/berichtsheft-sync
python3 -m berichtsheft init
python3 -m berichtsheft import data/shifts_kw23_24.json
pip install -r requirements.txt
npm install   # @cursor/sdk untuk /ai
```

`.env` (salin dari `.env.example`):

- `TELEGRAM_BOT_TOKEN` — dari @BotFather
- `TELEGRAM_ALLOWED_USER_ID` — opsional, batasi user
- `GEMINI_API_KEY` — polish teks + Vision foto
- `AI_VISION_ENABLED=true`
- `CURSOR_API_KEY` — untuk `/ai` (opsional)

## Jalankan

Terminal A:

```bash
python3 -m berichtsheft serve
```

Terminal B:

```bash
python3 -m berichtsheft bot
```

## API (`api_server.py`)

| Endpoint | Fungsi |
|----------|--------|
| `GET /health` | Status + gemini/vision/cursor |
| `POST /log` | Simpan work log |
| `POST /finish` | Orchestrator + worker (dry-run atau live via config) |
| `POST /approve` | Setujui draft; worker live jika `require_ok_before_submit` |
| `POST /correct` | Koreksi teks (Gemini) |
| `GET /status` | Ringkasan hari |
| `POST /vision/analyze` | Gemini Vision — foto → teks DE / log |
| `POST /ai` | Cursor SDK agent |

## Telegram

| Input | Hasil |
|-------|--------|
| Teks biasa | Work log (`POST /log`) |
| Foto + caption | `POST /vision/analyze` → log + lampiran |
| `/selesai [ringkasan]` | Draft + dry-run BLok (atau live jika `live_blok_after_finish: true`) |
| `/ok` | Approve; isi BLok live jika `require_ok_before_submit` + live flag |
| `/ubah …` | Koreksi satu pesan |
| `/ai …` | Cursor agent (1–5 menit) |
| `/status` | Ringkasan DB |

Caption foto yang didukung: `stichpunkte`, `berufsschule`, `edtime`, `lampiran` (lihat `ai_vision.py`).

## Uji cepat

```bash
python3 -m berichtsheft telegram-check
python3 -m berichtsheft gemini-check
python3 -m berichtsheft vision-check
python3 -m berichtsheft cursor-check
python3 -m berichtsheft test-flow
```

## Lanjut Fase 2

Lihat `docs/BLok_AUTOMATION.md` — isi BLok otomatis (presence, Lernort, Abteilung, audit).
