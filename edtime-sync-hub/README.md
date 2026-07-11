# edtime-sync-hub

**Repo terpisah** untuk sinkronisasi **edtime (iPhone) → Google Sheets → Cursor**.

Tidak termasuk WAHA, WhatsApp, Docker, atau Mac Automation Hub.  
Untuk integrasi Mac/WAHA/iPhone hub → lihat repo **`mac-iphone-automation`**.

---

## Apa ini?

| Fungsi | Keterangan |
|--------|------------|
| Google Sheet | Database jadwal edtime (11 tab) |
| Apps Script | Webhook `EdtimeWebApp.gs` |
| Mac agent | Fetch, process, export JSON untuk Cursor |
| iPhone | Shortcuts edtime-fetch + login assist |

**Sheet ID Anda:** `1so9zekw-afSOueqYLNpSl-gfStJc8FsyOknW3QDt5pM`

---

## Quick start

```bash
git clone https://github.com/Acimdamero/edtime-sync-hub.git
cd edtime-sync-hub

bash install-secrets.sh          # GOOGLE_SHEET_ID sudah pre-filled
bash mac/install.sh

# Deploy EdtimeWebApp.gs di Google Apps Script → Web App URL
bash set-webhook-url.sh 'https://script.google.com/macros/s/.../exec'

bash run-agent.sh                # pipeline agentic lengkap
~/.edtime-sync/run-edtime.sh monitor watch
```

---

## Struktur

```
edtime-sync-hub/
├── run-agent.sh              # orchestrator agentic (entry)
├── install-secrets.sh
├── set-webhook-url.sh
├── config/secrets.ready.env  # Sheet ID pre-filled
├── mac/scripts/run-edtime.sh # CLI: sync, fetch, export, monitor
├── google/apps-script/EdtimeWebApp.gs
├── iphone/                   # Shortcuts specs
└── docs/
```

---

## Perintah

```bash
~/.edtime-sync/run-edtime.sh sync full
~/.edtime-sync/run-edtime.sh export
~/.edtime-sync/run-edtime.sh monitor status
```

---

## Apps Script (copy 1 file)

**File:** `google/apps-script/EdtimeWebApp.gs`  
**Cursor:** `Cmd+P` → ketik `EdtimeWebApp`

---

## Hubungkan dengan mac-iphone-automation (opsional)

Repos **independen**. Jika punya Mac Hub + WAHA, keduanya bisa pakai Sheet yang sama — tanpa dependency code.

---

## Lisensi / Author

Bagian dari ekosistem Automation Acimdamero — edtime sync standalone.
