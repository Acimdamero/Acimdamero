# Gemini API (Fase A — polish Deutsch)

## Dapatkan API key (gratis / trial)

1. Buka **https://aistudio.google.com/apikey** (login Google)
2. **Create API key** → pilih project
3. Salin key (format panjang, bukan password BLok)

## Pasang di Mac (jangan di chat Cursor)

Edit `~/Projects/berichtsheft-sync/.env`:

```env
GEMINI_API_KEY=AIza...your_key_here
GEMINI_MODEL=gemini-1.5-flash
AI_POLISH_ENABLED=true
```

Cek:

```bash
cd ~/Projects/berichtsheft-sync
python3 -m berichtsheft gemini-check
```

Restart:

```bash
# Terminal serve + bot stop (Ctrl+C) lalu jalankan lagi
python3 -m berichtsheft serve
python3 -m berichtsheft bot
```

## Perilaku

| Perintah | Tanpa Gemini | Dengan Gemini |
|----------|--------------|---------------|
| `/selesai` | Kamus DE | Teks dirapikan AI |
| `/ubah …` | Tambah koreksi | Seluruh draft ditulis ulang formal DE |

## `/ubah` di Telegram

**Satu pesan**, contoh:

```
/ubah Bitte formell auf Deutsch mit Hotelfachbegriffen für die Ausbildung
```

❌ Salah: pesan 1 panjang, pesan 2 hanya `/ubah`

## Privasi

Teks Berichtsheft dikirim ke Google API. Jangan nama tamu / data sensitif.

## Matikan AI

```env
AI_POLISH_ENABLED=false
```

Atau hapus `GEMINI_API_KEY`.
