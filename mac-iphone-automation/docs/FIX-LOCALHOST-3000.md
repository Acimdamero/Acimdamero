# localhost:3000 Kosong / Tidak Muncul Apa-apa — Solusi

## Penyebab & Fix cepat

| Gejala | Penyebab | Solusi |
|--------|----------|--------|
| **Connection refused** | Docker belum jalan | Buka **Docker Desktop**, tunggu ikon 🐳 |
| **Halaman kosong / putih** | Butuh login (HTTP 401) | Buka `/dashboard` + login |
| **401 Unauthorized** | Normal — WAHA minta password | Lihat login di bawah |
| **QR tidak muncul** | Session belum start | Jalankan `bash start-waha.sh` |

---

## Fix 1 menit — jalankan di Terminal Mac

```bash
cd ~/Acimdamero/mac-iphone-automation
git pull origin cursor/mac-iphone-automation-hub-8703
bash start-waha.sh
```

Script ini:
- Nyalakan Docker
- Start WAHA
- Buka browser dashboard
- Tunggu QR

---

## URL yang BENAR (bukan cuma localhost:3000)

❌ `http://localhost:3000` → sering kosong / 401

✅ **`http://localhost:3000/dashboard`**

**Login:**
| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `change-me` |

Setelah login → **Sessions** → klik **default** → **QR muncul**

---

## Scan QR di iPhone

1. WhatsApp → **Settings** (⚙️)
2. **Linked Devices** / Perangkat Tertaut
3. **Link a Device** / Tautkan Perangkat
4. Scan QR di layar Mac

---

## Cek manual (Terminal Mac)

```bash
# Docker jalan?
docker ps | grep waha

# Port hidup? (401 = OK, 000 = mati)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/

# Start + QR
bash start-waha.sh
```

---

## Jika Docker Desktop belum terinstall

1. Download: https://www.docker.com/products/docker-desktop/
2. Install → buka Docker Desktop
3. Tunggu "Docker Desktop is running"
4. Ulangi `bash start-waha.sh`

---

## Alternatif: QR di Terminal (tanpa browser)

```bash
API_KEY=automation-hub-test-key

curl -X POST http://127.0.0.1:3000/api/sessions/start \
  -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"default"}'

# Tunggu 10 detik, lalu buka dashboard atau cek status:
curl http://127.0.0.1:3000/api/sessions/default -H "X-Api-Key: $API_KEY"
```

Status harus berubah: `SCAN_QR_CODE` → scan → `WORKING`

---

## Ringkasan

```
1. Docker Desktop ON
2. bash start-waha.sh
3. Browser: http://localhost:3000/dashboard
4. Login: admin / change-me
5. Sessions → default → QR
6. iPhone WhatsApp → Linked Devices → Scan
```
