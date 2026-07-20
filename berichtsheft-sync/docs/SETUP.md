# Panduan setup — urutan lengkap (hasil optimal)

Ikuti **nomor urut**. Jangan loncat ke Telegram sebelum `init` dan `credentials`.

---

## Fase 0 — Persiapan Mac (10 menit)

| # | Tindakan | Cek |
|---|----------|-----|
| 0.1 | Buka Terminal, masuk folder proyek | `cd ~/Projects/berichtsheft-sync` |
| 0.2 | Python 3.9+ | `python3 --version` |
| 0.3 | Buat venv (opsional) | `python3 -m venv .venv && source .venv/bin/activate` |
| 0.4 | Install dependensi | `pip install -r requirements.txt` |
| 0.5 | Playwright browser (untuk BLok nanti) | `playwright install chromium` |

**Mac sebagai stasiun robot:** System Settings → Battery → prevent sleep on power adapter (saat kerja).

---

## Fase 1 — Database & jadwal (5 menit)

| # | Perintah | Hasil |
|---|----------|-------|
| 1.1 | `python3 -m berichtsheft init` | DB + template + contoh KW23/24 |
| 1.2 | `python3 -m berichtsheft preview --date 2026-06-04` | Preview 1 hari |
| 1.3 | Import jadwal baru (minggu depan) | Salin `data/shifts_kw23_24.json` → edit → `python3 -m berichtsheft import data/shifts_NEU.json` |

---

## Fase 2 — Kredensial BLok di Keychain (sekali, 2 menit)

**Maksud Keychain:** Password disimpan di **brankas macOS**, hanya worker di Mac yang bisa baca. Anda **tidak** mengetik password di Telegram atau Cursor chat.

| # | Perintah |
|---|----------|
| 2.1 | `python3 -m berichtsheft credentials set --service blok` |
| 2.2 | Masukkan username BLok (terminal, tidak terlihat di chat) |
| 2.3 | Masukkan password BLok |
| 2.4 | Cek | `python3 -m berichtsheft credentials test --service blok` |

File `.env` hanya untuk **Telegram token**, bukan password BLok:

```bash
cp .env.example .env
# edit: TELEGRAM_BOT_TOKEN=... dari @BotFather
# edit: TELEGRAM_ALLOWED_USER_ID=... id numerik Anda
```

Cara dapat `TELEGRAM_ALLOWED_USER_ID`: jalankan bot sekali, kirim `/start` — lihat log API.

---

## Fase 3 — Peta area & jobdesk (15 menit, sekali)

| # | Tindakan |
|---|----------|
| 3.1 | Edit `data/areas_hotel.json` — isi zona hotel Anda (BRF, HK, Tagung, …) |
| 3.2 | Edit `data/templates_hotelfach.json` — kalimat nyata yang Anda lakukan |
| 3.3 | `python3 -m berichtsheft areas load` | Muat area ke DB |

---

## Fase 4 — Uji coba tanpa Telegram (5 menit)

Simulasi alur selesai kerja:

| # | Perintah |
|---|----------|
| 4.1 | `python3 -m berichtsheft log --date 2026-06-04 --text "Tagung coffee break"` |
| 4.2 | `python3 -m berichtsheft finish --date 2026-06-04 --summary "Selesai shift tagung"` |
| 4.3 | `python3 -m berichtsheft preview --date 2026-06-04` |
| 4.4 | `python3 -m berichtsheft worker --date 2026-06-04 --dry-run` |

Harus muncul file di `output/blok_dry_run/` (bukan isi web sungguhan).

---

## Fase 5 — Telegram bot (10 menit)

| # | Tindakan |
|---|----------|
| 5.1 | Buat bot di Telegram → @BotFather → `/newbot` → salin token ke `.env` |
| 5.2 | Jalankan API + bot (2 terminal atau satu): |

Terminal A:
```bash
python3 -m berichtsheft serve
```

Terminal B (atau sama):
```bash
python3 -m berichtsheft bot
```

| # | Di HP — uji |
|---|-------------|
| 5.3 | `/start` |
| 5.4 | `/log Bantu buffet pagi` |
| 5.5 | `/selesai` |
| 5.6 | Baca preview → `/ok` atau `/ubah singkat` |

---

## Fase 6 — BLok live (hati-hati, setelah dry-run OK)

| # | Perintah |
|---|----------|
| 6.1 | Discovery: login BLok manual sekali, catat URL form di `config.yaml` (salin dari `config.example.yaml`) |
| 6.2 | `python3 -m berichtsheft worker --date YYYY-MM-DD --live` |
| 6.3 | Cek di browser BLok apakah field terisi |
| 6.4 | Jika UI beda, sesuaikan selector di `berichtsheft/blok_worker.py` |

**Catatan:** Selector BLok perlu disesuaikan setelah Anda login pertama kali — v1 menyertakan **stub + dry-run**; live membutuhkan penyesuaian 1x di Mac.

---

## Fase 7 — WiFi portal perusahaan (opsional)

| # | Tindakan |
|---|----------|
| 7.1 | Salin `config.example.yaml` → `config.yaml` |
| 7.2 | Isi `wifi.ssid`, `wifi.portal_url`, `wifi.login_button_selector` |
| 7.3 | `python3 scripts/wifi_portal.py --dry-run` |
| 7.4 | Cron/launchd: lihat `docs/WIFI.md` |

---

## Fase 8 — Operasi harian (5 menit/hari)

| Waktu | Anda | Sistem |
|-------|------|--------|
| Minggu | Upload/import jadwal EdTime | Update `shifts` |
| Saat kerja | `/log …` di Telegram | Simpan log |
| Selesai shift | `/selesai` | Orchestrate + isi BLok (jika Mac online) |
| Malam | `/ok` atau `/ubah …` | Finalize / perbaiki |

Mac harus **online** saat `/selesai` jika ingin auto-isi BLok langsung.

---

## Troubleshooting

| Gejala | Solusi |
|--------|--------|
| Worker gagal login | `credentials test`; cek password Keychain |
| Bot tidak jawab | Cek `TELEGRAM_BOT_TOKEN`, `serve` jalan |
| BLok tidak terisi | Gunakan `--dry-run` dulu; sesuaikan selector |
| Mac sleep | Charger + disable sleep |

---

## Checklist sebelum produksi

- [ ] `init` sukses
- [ ] `credentials set` blok
- [ ] `finish` + `preview` sukses
- [ ] `worker --dry-run` menghasilkan file
- [ ] Telegram `/log` + `/selesai` + `/ok`
- [ ] BLok live diuji 1 hari
- [ ] areas_hotel.json diisi
