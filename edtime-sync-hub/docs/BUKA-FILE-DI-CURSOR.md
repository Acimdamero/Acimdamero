# Buka file di Cursor — panduan singkat

## 1. `secrets.env` (config Mac)

**Lokasi asli di Mac (bukan di repo):**
```
/Users/ANDA/.edtime-sync/secrets.env
```

**Cara buat otomatis (tanpa nano):**
```bash
cd mac-iphone-automation
bash install-secrets.sh
```

**Buka di Cursor:**
1. Menu **File → Open File...** (Mac: `Cmd + O`)
2. Tekan `Cmd + Shift + G` → paste: `~/.edtime-sync/secrets.env`
3. Enter

**Atau cepat:** `Cmd + P` → ketik `secrets.env`

**File template di repo (sudah diisi Sheet ID):**
```
mac-iphone-automation/config/secrets.ready.env
```
Buka dengan `Cmd + P` → ketik `secrets.ready`

---

## 2. `EdtimeWebApp.gs` (Apps Script)

**Lokasi di repo Cursor:**
```
mac-iphone-automation/google/apps-script/EdtimeWebApp.gs
```

**Buka di Cursor:**
1. `Cmd + P` (Quick Open)
2. Ketik: `EdtimeWebApp`
3. Enter

**Atau sidebar kiri:**
```
mac-iphone-automation
  └── google
        └── apps-script
              └── EdtimeWebApp.gs   ← klik
```

**Copy ke Google Apps Script:**
1. Buka file di Cursor
2. `Cmd + A` (select all) → `Cmd + C` (copy)
3. Browser → Google Sheet → Extensions → Apps Script
4. Hapus isi Code.gs → `Cmd + V` paste → Save → Deploy

---

## 3. Urutan kerja

| # | File | Aksi |
|---|------|------|
| 1 | Terminal | `bash install-secrets.sh` |
| 2 | `EdtimeWebApp.gs` | Copy → paste ke Google Apps Script → Deploy |
| 3 | Terminal | `bash set-webhook-url.sh 'URL_WEB_APP'` |
| 4 | Terminal | `bash run-agent.sh` |
