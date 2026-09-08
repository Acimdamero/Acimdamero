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

## Cloud Agent vs Mac

WAHA = Docker + scan QR Linked Devices. **Cloud Agent VM biasanya tidak punya Docker/WAHA** (port `3000` mati). Di cloud kita hanya bisa:

- tulis `WHATSAPP_ALLOWED_NUMBER` di `.env` (gitignored)
- jalankan API `serve` di `:8765`
- **tidak** bisa `wa-bot` / `wa-menu-push` sampai WAHA hidup di Mac Anda

Jalankan langkah di bawah **di Mac** (satu kali pair QR, lalu bot lokal).

---

## Setup (Mac) — copy-paste

### 1. Jalankan WAHA + scan QR

```bash
cd mac-iphone-automation   # atau path repo hub Anda
docker compose -f docker/docker-compose.waha.yml up -d
```

1. Buka http://localhost:3000 (dashboard WAHA)
2. Login dashboard jika diminta (`WAHA_DASHBOARD_*` di compose)
3. iPhone → WhatsApp → **Linked Devices** → **Link a Device** → scan QR
4. Tunggu session status `WORKING`

### 2. Isi `.env` di berichtsheft-sync

```bash
cd berichtsheft-sync
cp -n .env.example .env   # jika belum ada
```

Edit `.env` (nomor tanpa `+` / spasi, format `628…` — contoh `6281234567890`):

```
WHATSAPP_ALLOWED_NUMBER=628…
WAHA_BASE_URL=http://127.0.0.1:3000
WAHA_SESSION=default
WAHA_API_KEY=change-me-in-production
BERICHTSHEFT_API=http://127.0.0.1:8765
```

Jangan commit `.env`. Cloud Agent menulis nomor Anda ke `.env` lokal (gitignored); di Mac salin nilai yang sama.

### 3. Jalankan API + bot WA

**Terminal A:**
```bash
cd berichtsheft-sync
python3 -m berichtsheft serve
```

**Terminal B:**
```bash
cd berichtsheft-sync
python3 -m berichtsheft wa-bot
```

Atau satu runner:

```bash
./scripts/run_local.sh whatsapp
```

Cek + kirim menu ke `628…@c.us` (dari `WHATSAPP_ALLOWED_NUMBER`):

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
