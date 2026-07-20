# BLok live — isi web otomatis

## Prasyarat

- ✅ `python3 -m berichtsheft credentials test --service blok`
- ✅ `config.yaml` ada (sudah disalin; **selectors** mungkin perlu disesuaikan)

## Langkah 1 — Discovery selector (sekali, ~15 menit)

1. Buka Chrome → login **BLok** manual:  
   https://www.online-ausbildungsnachweis.de
2. Buka halaman **isi laporan harian** (sama seperti biasa Anda isi).
3. Tekan **F12** → tab **Elements**.
4. Klik ikon panah → pilih:
   - kotak **teks aktivitas** (textarea)
   - tombol **simpan**
5. Di Elements, klik kanan elemen → **Copy** → **Copy selector**.
6. Tempel ke `config.yaml` di bagian `blok.selectors`:

```yaml
    activity_text: 'textarea#...'   # dari Copy selector
    save_button: 'button#...'
```

7. Untuk login (jika worker perlu isi form):
   - `username`, `password`, `login_button` sama cara copy selector.

Simpan file.

## Langkah 2 — Dry-run dulu

```bash
cd ~/Projects/berichtsheft-sync
python3 -m berichtsheft finish --date 2026-06-06 --fill
open output/blok_dry_run/2026-06-06.html
```

## Langkah 3 — Live (browser sungguhan)

```bash
python3 -m berichtsheft serve    # terminal 1
python3 -m berichtsheft bot      # terminal 2 (opsional)

python3 -m berichtsheft worker --date 2026-06-06 --live
```

Cek:

- Screenshot: `output/blok_dry_run/2026-06-06_live.png`
- Login manual di BLok: apakah field terisi?

## Langkah 4 — Dari Telegram

Setelah selector benar:

1. `/log` … saat kerja
2. `/selesai` → dry-run HTML
3. Set `orchestrator.auto_fill_blok_after_finish` + ubah API untuk `--live` (lanjutan v2)

Saat ini `/selesai` di bot = **dry-run**; live = perintah `worker --live` di Mac atau kita aktifkan flag live nanti.

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Login gagal | `credentials test`; cek password Keychain |
| Field kosong | Selector salah — ulangi F12 |
| Tanggal libur | Import jadwal; hari `arbeit` saja |
