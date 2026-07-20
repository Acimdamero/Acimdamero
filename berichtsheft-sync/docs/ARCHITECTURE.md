# Arsitektur — Mac, Keychain, Bot, Worker

## Mengapa MacBook “ikut”?

BLok diakses lewat **browser + sesi login**. Worker menjalankan browser (Playwright) di mesin yang **punya kredensial dan bisa online**.

```
[iPhone Telegram] ──internet──► [MacBook: API + Worker + Keychain]
                                      │
                                      ▼
                              [BLok di browser]
```

Bot bisa di mana saja; **yang menulis ke BLok** harus di mesin yang menjalankan browser worker.

---

## Keychain — ideal vs “kurang ideal”

### Ideal (disarankan untuk Anda)

| Aspek | Penjelasan |
|-------|------------|
| **Penyimpanan** | Username/password BLok di **macOS Keychain** (`berichtsheft-sync` service) |
| **Worker** | Jalan di **MacBook yang sama** |
| **Keamanan** | Password dienkripsi OS; tidak masuk repo, tidak masuk chat Cursor, tidak ke prompt AI |
| **Anda** | Set **sekali** di Terminal Mac: `credentials set` |
| **Operasi harian** | Hanya HP → Telegram; Mac cukup **menyala + tidak sleep** (charger) |

Alur: Worker baca Keychain → login BLok → isi form → kirim preview ke Telegram → Anda `OK` (5 menit).

### Kurang ideal (VPS + headless)

| Aspek | Masalah |
|-------|---------|
| Keychain | **Khusus macOS** — VPS Linux tidak punya Keychain Anda |
| Alternatif VPS | Password di `.env` di server cloud → lebih besar risiko bocor, backup server, hukum data |
| Browser headless di cloud | Kadang BLok deteksi bot / IP beda negara |
| Maintenance | Dua mesin (Mac + VPS) |

**Kesimpulan ideal:** Satu Mac sebagai **“stasiun robot”** (API + worker + Keychain). HP hanya bot. Tailscale opsional agar API aman dari internet.

### PC kantor / Cursor Cloud (bukan stasiun robot)

Edit **katalog kegiatan** di kantor lewat GitHub saja — **jangan** jalankan bot/BLok/Keychain di PC kantor, dan **jangan** sambungkan LAN kantor ke MacBook. Panduan: [DUA_KOMPUTER.md](DUA_KOMPUTER.md).

---

## Komponen

| Modul | File | Fungsi |
|-------|------|--------|
| Credentials | `credentials.py` | Keychain get/set |
| DB | `db.py` | shifts, logs, drafts, approvals |
| Orchestrator | `orchestrator.py` | Gabung log + shift → draft DE |
| API | `api_server.py` | REST untuk bot / health |
| Telegram | `telegram_bot.py` | /log, /selesai, /ok |
| BLok worker | `blok_worker.py` | Playwright login + isi (dry-run/live) |
| WiFi | `scripts/wifi_portal.py` | Portal klik login |
| Generator | `generator.py` | Template + shift |

---

## Status otomasi (level)

| Level | Kondisi |
|-------|---------|
| L0 | Generate teks saja |
| L1 | Auto-isi BLok draft setelah `/selesai` |
| L2 | Auto-submit setelah `/ok` |
| L3 | Tanpa laporan — **nonaktif** |
