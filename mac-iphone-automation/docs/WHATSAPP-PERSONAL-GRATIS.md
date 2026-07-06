# WhatsApp Personal Gratis — Panduan Cepat

Cara **kirim WA personal tanpa bayar per pesan** lewat Automation Hub.

---

## Pilihan gratis

| Metode | Biaya | Auto kirim? | Baca inbox? | Cocok untuk |
|--------|-------|-------------|-------------|-------------|
| **WAHA (self-host)** | **Rp 0** | ✅ | ✅ | ⭐ Otomatisasi personal penuh |
| Shortcuts + wa.me | Rp 0 | ❌ (1 tap Send) | ❌ | Pesan sesekali |
| Meta Cloud API | Free tier terbatas* | ✅ | ✅ | Bisnis, bukan chat personal biasa |

\*Meta free tier = conversation bisnis, butuh setup WABA — **bukan** pengganti chat personal harian gratis.

**Rekomendasi untuk Anda:** **WAHA** — gratis, nomor personal, kirim + terima otomatis.

---

## Setup 10 menit (gratis total)

### 1. Docker WAHA di Mac

```bash
cd mac-iphone-automation
docker compose -f docker/docker-compose.waha.yml up -d
```

Buka http://localhost:3000

### 2. Pair nomor personal (scan QR)

WhatsApp iPhone → **Settings → Linked Devices → Link a Device**  
Scan QR di dashboard WAHA (sekali saja).

### 3. Config Hub — mode gratis personal

```bash
cp config/config.example.env ~/.automation-hub/config.env
```

Pastikan isi:

```bash
WHATSAPP_BACKEND=waha
WAHA_BASE_URL=http://localhost:3000
WAHA_SESSION=default
WAHA_API_KEY=change-me-in-production   # ganti di docker-compose
```

Simpan key ke Keychain:

```bash
security add-generic-password -s automation-hub -a waha-api-key -w "API_KEY_ANDA"
```

### 4. Test kirim gratis

```bash
~/.automation-hub/run-task.sh waha-send 628NOMOR_ANDA "Test gratis dari Hub"
```

Atau:

```bash
~/.automation-hub/run-task.sh whatsapp-send 628NOMOR_ANDA "Test"
# Otomatis pakai WAHA karena WHATSAPP_BACKEND=waha
```

---

## Kirim ke siapa saja (personal)

Format nomor Indonesia:

```
6281234567890@c.us
```

Di command Hub cukup:

```bash
waha-send 6281234567890 "Halo, pesan personal gratis"
```

**Gratis** — tidak ada biaya per pesan. Hanya pakai internet + Mac nyala.

---

## Otomatis dari Google Sheet (gratis)

Tab `Queue`:

| device | command | status | args |
|--------|---------|--------|------|
| mac | waha-send | pending | 628xxx\|Pesan otomatis personal |

Mac daemon poll → kirim via WAHA → **Rp 0**.

---

## Terima & balas pesan masuk (gratis)

1. Set webhook WAHA di `docker-compose.waha.yml`:

```yaml
WAHA_WEBHOOK_URL: https://script.google.com/macros/s/WEB_APP_ID/exec
WAHA_WEBHOOK_EVENTS: message,message.any
```

2. Redeploy Apps Script (`QueueSync.gs` + `WhatsAppInbound.gs`)
3. Pesan masuk → tab Sheet **`Inbox`**
4. Auto-reply (gratis):

Tambah baris Sheet:

| device | command | status | args |
|--------|---------|--------|------|
| mac | waha-send | pending | NOMOR_PENGIRIM\|Balasan otomatis |

---

## Biaya nyata = Rp 0

| Item | Biaya |
|------|-------|
| WAHA software | Gratis (open source) |
| Docker di Mac | Gratis |
| Pesan WA | Gratis (pakai kuota internet) |
| Google Sheet antrian | Gratis |
| Pushcut (opsional) | ~$2.49/bln — **tidak wajib** untuk WA |

**Total wajib: Rp 0**

---

## Aturan aman (supaya nomor tidak kena ban)

WAHA gratis tapi **unofficial** — jaga nomor personal:

| ✅ Aman | ❌ Hindari |
|---------|-----------|
| Balasan otomatis ke kontak kenal | Spam ratusan orang/hari |
| Notifikasi backup/status ke diri sendiri | Broadcast massal |
| Max ~20–50 pesan/jam | Pesan identik ke banyak nomor |
| Jeda 2–5 detik antar pesan | Marketing tanpa izin |

---

## Perbandingan singkat

```
Butuh GRATIS + PERSONAL + AUTO KIRIM  →  WAHA ✅
Butuh GRATIS + sesekali manual         →  wa.me Shortcuts ✅
Butuh bisnis resmi + scale             →  Meta API (bukan fokus personal gratis)
```

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Session disconnected | Scan QR ulang di dashboard |
| 401 error | Cek `WAHA_API_KEY` sama dengan docker-compose |
| Pesan tidak terkirim | `waha-status` — pastikan session WORKING |
| Docker tidak jalan | Buka Docker Desktop dulu |

---

## Command cheat sheet

```bash
# Kirim personal gratis
run-task.sh waha-send 628xxx "Halo"

# Cek WAHA online
run-task.sh waha-status

# Backup Mac + WA gratis ke nomor sendiri
run-task.sh backup all && run-task.sh waha-send 628YOURNUMBER "Backup selesai ✅"
```

---

**Kesimpulan:** Untuk **kirim personal gratis + otomatis**, pasang **WAHA** — sudah terintegrasi Hub, biaya **Rp 0**, tanpa Meta Business.
