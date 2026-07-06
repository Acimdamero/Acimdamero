# Panduan Shortcuts iPhone — Automation Hub

## Prasyarat Mac

1. Jalankan `bash mac/install.sh` di Mac
2. **System Settings → General → Sharing → Remote Login** = ON
3. Catat hostname Mac (mis. `MacBook-Pro.local`)

---

## Shortcut 1: Status Mac (SSH)

1. Shortcuts → **+** → nama: **Hub — Status Mac**
2. Tambah action: **Run Script Over SSH**
3. Konfigurasi:
   - **Host:** `MacBook-Pro.local` (ganti dengan hostname Anda)
   - **Port:** `22`
   - **User:** username macOS Anda
   - **Authentication:** SSH Key → Copy Public Key → paste ke Mac:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
pbpaste >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

4. **Script:**

```bash
~/.automation-hub/run-task.sh status
```

5. Tambah **Show Result** atau **Quick Look**

---

## Shortcut 2: Backup Mac

**Script SSH:**

```bash
~/.automation-hub/run-task.sh backup all
```

Pin ke Home Screen atau Siri: *"Hey Siri, backup Mac"*

---

## Shortcut 3: Sleep / Wake Mac

**Sleep:**

```bash
~/.automation-hub/run-task.sh sleep
```

**Wake:**

```bash
~/.automation-hub/run-task.sh wake
```

---

## Shortcut 4: Kontrol App Mac

**Buka Safari:**

```bash
~/.automation-hub/run-task.sh open-app Safari
```

**Tutup Spotify:**

```bash
~/.automation-hub/run-task.sh quit-app Spotify
```

---

## Shortcut 5: Cursor Workflow (dari iPhone)

**Git pull project:**

```bash
~/.automation-hub/run-task.sh cursor-pull ~/Developer/NAMA-PROJECT
```

**Build project:**

```bash
~/.automation-hub/run-task.sh cursor-build ~/Developer/NAMA-PROJECT
```

---

## Automation: Polling antrian iPhone (Mac → iPhone)

Agar Mac bisa "memerintah" iPhone:

1. Deploy Google Apps Script (lihat `google/SHEET-TEMPLATE.md`)
2. Buat Shortcut **Hub — Process iPhone Queue**:
   - **Get contents of URL:** `{WEB_APP_URL}?device=iphone`
   - **Get Dictionary from Input**
   - **Repeat with Each** item in `pending`:
     - **If** command = `notify` → **Show Notification** (args)
     - **If** command = `open-url` → **Open URL** (args)
     - **If** command = `run-shortcut` → **Run Shortcut** (args)
     - **Get contents of URL:** mark done (via Apps Script function atau update Sheet manual)
3. **Automation** → **Time of Day** setiap 15 menit → jalankan shortcut (tanpa konfirmasi)

---

## Akses jarak jauh (luar Wi‑Fi rumah)

1. Install [Tailscale](https://tailscale.com) di Mac + iPhone
2. Ganti Host SSH dengan MagicDNS Mac (mis. `macbook.tail12345.ts.net`)
3. Tambah di awal shortcut: **Connect to Tailscale** (action bawaan)

---

## Keamanan

- Gunakan **SSH Key**, bukan password
- Jangan simpan password Google/1Password di teks Shortcut
- Token API simpan di **Keychain iPhone** (Variables → Ask Each Time)
