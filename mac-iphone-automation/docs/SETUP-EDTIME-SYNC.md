# Setup edtime Sync — iPhone → Cursor

Panduan lengkap setup otomatis sinkronisasi data **edtime** dari iPhone ke **Cursor** (Mac/iOS) via Google Sheet + Drive.

---

## Prasyarat

| Item | Wajib |
|------|-------|
| Mac dengan Automation Hub terinstall | ✅ |
| iPhone dengan app **edtime Mitarbeiter-App** | ✅ |
| Akun edtime dari employer | ✅ |
| Google Drive (Mac + iPhone, akun sama) | ✅ |
| Google Sheet Automation Queue | ✅ |
| Apps Script deployed (Web App URL) | ✅ |

---

## Langkah 1 — Setup Mac (sekali)

```bash
cd mac-iphone-automation
bash setup-edtime-sync.sh
```

Script ini akan:
- Copy script `edtime-*.sh` ke `~/.automation-hub/scripts/`
- Buat `edtime-mapping.json`
- Buat folder `Automation Hub/Edtime/` di Google Drive
- Simpan Webhook URL di Keychain Mac

---

## Langkah 2 — Apps Script + Sheet tabs

1. Buka Spreadsheet **Automation Queue**
2. **Extensions → Apps Script**
3. Paste **3 file** (project yang sama):
   - `google/apps-script/QueueSync.gs`
   - `google/apps-script/EdtimeSync.gs`
   - `google/apps-script/WhatsAppInbound.gs` (opsional)
4. **Deploy → New deployment → Web app**
   - Execute as: **Me**
   - Access: **Anyone** (atau hanya Anda)
5. Salin URL → jalankan di Mac:

```bash
~/.automation-hub/scripts/edtime-save-credentials.sh webhook 'URL_ANDA'
```

6. Buat tab Sheet — lihat [`google/SHEET-EDTIME-TABS.md`](../google/SHEET-EDTIME-TABS.md)

---

## Langkah 3 — Login edtime di iPhone (auto session)

> **Auto login penuh tidak mungkin di iOS** — Apple wajibkan Face ID/tap untuk password.

**Yang kita setup:**

1. **Login manual sekali** di app edtime
2. App **menyimpan session** — fetch berikutnya langsung ke dashboard
3. Shortcut **Login Assist** jika session expired (Passwords iOS 18+)

Ikuti: [`iphone/EDTIME-SHORTCUTS-SETUP.md`](../iphone/EDTIME-SHORTCUTS-SETUP.md)

---

## Langkah 4 — Shortcuts iPhone

Buat 3 shortcut utama:

| Shortcut | Spec file |
|----------|-----------|
| Hub — edtime Fetch | `iphone/edtime-fetch.shortcut-spec.json` |
| Hub — edtime Login Assist | `iphone/edtime-login-assist.shortcut-spec.json` |
| Hub — Process iPhone Queue | `iphone/SHORTCUTS-GUIDE.md` (tambah handler edtime-*) |

Tambahkan handler di **Hub — Execute Command**:

```
If command = edtime-open → Open App edtime
If command = edtime-fetch → Run Shortcut Hub — edtime Fetch
If command = edtime-login → Run Shortcut Hub — edtime Login Assist
```

Update `command-registry.json` sudah termasuk perintah edtime.

---

## Langkah 5 — Automation iPhone (polling)

**Shortcuts → Automation → + → Time of Day → Every 15 minutes**

- Run: **Hub — Process iPhone Queue**
- Run Immediately: **ON**
- (Opsional) Only on Home WiFi

Atau **Pushcut** untuk trigger instant dari Mac:

```bash
~/.automation-hub/run-task.sh iphone-dispatch edtime-fetch week=current
```

---

## Langkah 6 — Test pipeline

```bash
# Buka edtime di iPhone
~/.automation-hub/run-task.sh edtime-open

# Minta iPhone fetch (SS + input jadwal)
~/.automation-hub/run-task.sh edtime-fetch week=current

# Pipeline lengkap: fetch → process → export Cursor
~/.automation-hub/run-task.sh edtime-sync full

# Cek export
~/.automation-hub/run-task.sh edtime-status
```

---

## Langkah 7 — Cursor iOS / Cursor Mac baca data

### Opsi A — Google Drive MCP (disarankan)

1. Copy MCP config:

```bash
mkdir -p ~/.cursor
cp mac-iphone-automation/cursor/mcp.json.example ~/.cursor/mcp.json
```

2. Restart Cursor → authenticate Google Drive
3. Minta agent: *"Baca Automation Hub/Edtime/cursor/latest.json dan ringkas jadwal minggu ini"*

### Opsi B — Sheet tab CursorExportRows

Buka Google Sheet → tab `CursorExportRows` → copy ke Cursor chat.

### Opsi C — Web App JSON

```bash
curl "$(security find-generic-password -s automation-hub -a webhook-url -w)?action=cursor-edtime-export"
```

---

## Perintah run-task edtime

| Perintah | Fungsi |
|----------|--------|
| `edtime-open` | Dispatch buka edtime di iPhone |
| `edtime-fetch [week=current]` | Dispatch fetch SS + jadwal |
| `edtime-sync full` | Pipeline lengkap |
| `edtime-process` | Proses inbox Drive + merge Sheet |
| `edtime-export` | Buat `latest.json` untuk Cursor |
| `edtime-status` | Ringkasan export |
| `edtime-credentials webhook <url>` | Simpan webhook Keychain |

---

## Alur SS (Screenshot) otomatis

Karena iOS **tidak bisa** screenshot app lain sepenuhnya otomatis:

1. Shortcut **buka edtime**
2. **Notifikasi**: "Screenshot Schichtplan sekarang"
3. Anda **1 tap** Vol Up + Side Button
4. Shortcut **ambil foto terbaru** dari album Screenshots
5. **Simpan** ke `iCloud Drive/Automation Hub/Edtime/Screenshots/`
6. **POST metadata** + form jadwal ke Sheet
7. Mac **process + export** ke Cursor

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Session edtime expired | Jalankan `edtime-login` shortcut |
| Fetch timeout | Perbesar `EDTIME_FETCH_TIMEOUT` di config.env |
| Sheet kosong | Cek Webhook URL + deploy Apps Script ulang |
| Cursor tidak baca file | Pastikan Google Drive Desktop sync folder Edtime |
| SS tidak ketemu | Ambil SS dalam 5 menit sebelum shortcut lanjut |

---

## Keamanan

- ❌ Jangan simpan password edtime di Sheet atau git
- ✅ Webhook URL di Keychain Mac
- ✅ Password edtime di iOS Passwords / 1Password
- ✅ Sheet share hanya akun Anda

---

## Referensi

- [`EDTIME-BERICHTSHEFT-ARCHITECTURE.md`](EDTIME-BERICHTSHEFT-ARCHITECTURE.md)
- [`IPHONE-ARCHITECTURE-MAP.md`](IPHONE-ARCHITECTURE-MAP.md)
- [`ACCOUNTS.md`](ACCOUNTS.md)
