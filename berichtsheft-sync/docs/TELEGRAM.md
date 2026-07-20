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
2. **Start** → `/start` → catat **User ID** → isi di `.env` → restart bot
3. Saat kerja: kirim teks atau `/log …`
4. Selesai: `/selesai`
5. Cek preview → `/ok`

## Perintah

| Perintah | Fungsi |
|----------|--------|
| teks biasa | Sama seperti `/log` |
| `/log …` | Catatan kerja |
| `/selesai` | Draft + dry-run BLok |
| `/status` | Status hari ini |
| `/ok` | Setujui |
| `/ubah …` | Koreksi |
