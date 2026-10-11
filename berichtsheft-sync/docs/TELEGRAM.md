# Telegram — setup 10 menit

## 1. Buat bot

1. Buka Telegram → cari **@BotFather**
2. Kirim `/newbot`
3. Nama tampilan + username (harus berakhiran `bot`)
4. Salin **token** (contoh: `7123456789:AAH...`)

## 2. File `.env` di Mac

```bash
cd ~/Projects/berichtsheft-sync
python3 -m berichtsheft telegram-init
```

Buka `.env` di Cursor/VS Code, isi:

```
TELEGRAM_BOT_TOKEN=token_dari_BotFather
TELEGRAM_ALLOWED_USER_ID=
BERICHTSHEFT_API=http://127.0.0.1:8765
```

`TELEGRAM_ALLOWED_USER_ID` kosong dulu — setelah `/start` bot akan kirim ID Anda.

## 3. Cek

```bash
python3 -m berichtsheft telegram-check
```

Harus: API ✓ dan Bot @username ✓

## 4. Jalankan (2 terminal)

**Terminal A:**
```bash
python3 -m berichtsheft serve
```

**Terminal B:**
```bash
python3 -m berichtsheft bot
```

Mac harus online; API di `127.0.0.1:8765`.

## 5. Di HP

1. Cari bot Anda (username dari BotFather)
2. **Start** → `/start` → muncul **tombol menu** di bawah chat + User ID
3. Isi `TELEGRAM_ALLOWED_USER_ID` di `.env` → restart bot
4. Saat kerja: ketuk **📝 Log** lalu kirim teks, atau kirim teks langsung
5. Selesai: ketuk **✅ Selesai** → cek preview → **👍 OK**

## Menu tombol (Reply Keyboard)

Setelah `/start` atau `/menu`, keyboard tetap di bawah chat.

**Kalau tombol belum muncul:** bot lama masih jalan. Di Mac:

```bash
cd ~/Projects/berichtsheft-sync   # atau folder salinan Anda
git pull
./scripts/run_local.sh
# atau:
python3 -m berichtsheft menu-push
```

Lalu di HP kirim `/start` atau `/menu`.

| Tombol | Aksi |
|--------|------|
| 📝 Log | Minta Anda kirim teks kegiatan |
| ✅ Selesai | `/selesai` |
| 📊 Status | `/status` |
| 👍 OK | `/ok` |
| 📅 Minggu | `/minggu` |
| 🔍 Audit | `/audit` |
| 📷 Foto | Bantuan foto |
| 📎 Lampiran | `/lampiran` |
| ✏️ Ubah | Petunjuk `/ubah …` |
| 🤖 AI | Petunjuk `/ai …` |
| ❓ Help | `/help` |
| ☰ Menu | Tampilkan lagi keyboard + bantuan |

Label tombol bisa diubah nanti di `berichtsheft/telegram_bot.py` (`BTN_*` + `MENU_ACTIONS`).

### Jalankan lokal (satu perintah)

```bash
cd berichtsheft-sync
# isi TELEGRAM_BOT_TOKEN di .env
chmod +x scripts/run_local.sh
./scripts/run_local.sh
```

Ini menjalankan API + bot, memasang menu ☰, dan mengirim ulang keyboard ke chat terakhir.

## Perintah

| Perintah | Fungsi |
|----------|--------|
| teks biasa | Sama seperti `/log` |
| `/log …` | Catatan kerja |
| `/selesai` | Draft + dry-run BLok |
| `/status` | Status hari ini |
| `/ok` | Setujui |
| `/ubah …` | Koreksi |
| `/menu` | Tampilkan tombol keyboard |
