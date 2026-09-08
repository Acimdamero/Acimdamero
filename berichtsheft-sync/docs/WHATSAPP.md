# WhatsApp — bot Berichtsheft (nomor personal via WAHA)

Bot WhatsApp memakai **WAHA** (WhatsApp HTTP API self-host) yang sama dengan Automation Hub Anda. Nomor personal di-pair sekali (scan QR), lalu Berichtsheft balas lewat WhatsApp.

> Bukan Meta Cloud API bisnis. Gratis self-host; risiko ToS WhatsApp (unofficial) — pakai bijak.

---

## Alur

```
[WhatsApp iPhone Anda]
        │
        ▼
[WAHA Docker di Mac :3000]
        │  webhook atau polling
        ▼
[berichtsheft serve :8765 + wa-bot]
        │
        ▼
[SQLite + BLok worker]  (sama seperti Telegram)
```

Menu di WA dikirim sebagai **teks bernomor** (WhatsApp tidak punya ReplyKeyboard seperti Telegram).

---

## Setup (Mac)

### 1. Jalankan WAHA

```bash
cd mac-iphone-automation   # atau path repo hub Anda
docker compose -f docker/docker-compose.waha.yml up -d
```

Buka http://localhost:3000 → scan QR (WhatsApp → Linked Devices).

### 2. Isi `.env` di berichtsheft-sync

```bash
cd berichtsheft-sync
cp .env.example .env   # jika belum
```

```
WHATSAPP_ALLOWED_NUMBER=
WAHA_BASE_URL=http://127.0.0.1:3000
WAHA_SESSION=default
WAHA_API_KEY=change-me-in-production
BERICHTSHEFT_API=http://127.0.0.1:8765
```

Isi `WHATSAPP_ALLOWED_NUMBER` dengan nomor WhatsApp Anda (tanpa `+`, contoh `628…`).

### 3. Jalankan API + bot WA

**Terminal A:**
```bash
python3 -m berichtsheft serve
```

**Terminal B:**
```bash
python3 -m berichtsheft wa-bot
```

Cek:
```bash
python3 -m berichtsheft wa-check
python3 -m berichtsheft wa-menu-push
```

### 4. Webhook (opsional, lebih responsif)

Di `docker-compose.waha.yml` / env WAHA:

```
WAHA_WEBHOOK_URL=http://host.docker.internal:8765/whatsapp/webhook
WAHA_WEBHOOK_EVENTS=message
```

Restart WAHA. Endpoint juga tersedia di `/waha/webhook`.

---

## Perintah di WhatsApp

| Kirim | Arti |
|-------|------|
| `menu` / `m` / `/menu` | Tampilkan menu |
| `1` | Prompt log |
| `2` | `/selesai` |
| `3` | `/status` |
| `4` | `/ok` |
| `5` | `/minggu` |
| `6` | `/audit` |
| teks biasa | = `/log …` |
| `/selesai` `/ok` `/ubah …` | Sama seperti Telegram |

---

## Keamanan

- Hanya nomor di `WHATSAPP_ALLOWED_NUMBER` yang dilayani
- Jangan commit `.env`
- WAHA + nomor personal = grey area ToS — jangan spam / jangan bagikan API ke publik

---

## Troubleshooting

| Gejala | Cek |
|--------|-----|
| `wa-check` gagal | Docker WAHA hidup? Port 3000? `WAHA_API_KEY` cocok? |
| Bot tidak balas | `WHATSAPP_ALLOWED_NUMBER` benar (628…)? `serve` + `wa-bot` jalan? |
| Menu tidak datang | `wa-menu-push` · pastikan session WAHA `WORKING` |
| Konflik dengan Automation Hub | Satu proses WAHA; boleh share session `default` |
