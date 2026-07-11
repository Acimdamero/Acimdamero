# Setup edtime Sync — iPhone → Cursor

Panduan lengkap setup otomatis sinkronisasi data **edtime** dari iPhone ke **Cursor** (Mac/iOS) via Google Sheet + Drive.

---

## Prasyarat

| Item | Wajib |
|------|-------|
| Mac dengan edtime-sync-hub terinstall | ✅ |
| iPhone dengan app **edtime Mitarbeiter-App** | ✅ |
| Akun edtime dari employer | ✅ |
| Google Drive (Mac + iPhone, akun sama) | ✅ |
| Google Sheet Automation Queue | ✅ |
| Apps Script deployed (Web App URL) | ✅ |

---

## Langkah 1 — Setup Mac (sekali)

```bash
cd edtime-sync-hub
bash install-secrets.sh
bash mac/install.sh
bash setup-edtime-sync.sh
```

Script ini akan:
- Copy script `edtime-*.sh` ke `~/.edtime-sync/scripts/`
- Buat `edtime-mapping.json`
- Buat folder `Edtime Sync/` di Google Drive
- Simpan Webhook URL di Keychain Mac

---

## Langkah 2 — Apps Script + Sheet tabs

1. Buka Spreadsheet **Automation Queue**
2. **Extensions → Apps Script**
3. Paste **1 file**:
   - `google/apps-script/EdtimeWebApp.gs`
4. **Deploy → New deployment → Web app**
   - Execute as: **Me**
   - Access: **Anyone** (atau hanya Anda)
5. Salin URL → jalankan di Mac:

```bash
~/.edtime-sync/scripts/edtime-save-credentials.sh webhook 'URL_ANDA'
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

Polling antrian iPhone: lihat [`iphone/EDTIME-SHORTCUTS-SETUP.md`](../iphone/EDTIME-SHORTCUTS-SETUP.md)

---

## Langkah 5 — Automation iPhone (polling)

**Shortcuts → Automation → + → Time of Day → Every 15 minutes**

- Run: **Hub — Process iPhone Queue**
- Run Immediately: **ON**
- (Opsional) Only on Home WiFi

Atau **Pushcut** untuk trigger instant dari Mac:

```bash
~/.edtime-sync/run-edtime.sh fetch week=current
```

---

## Langkah 6 — Test pipeline

```bash
# Buka edtime di iPhone
~/.edtime-sync/run-edtime.sh open

# Minta iPhone fetch (SS + input jadwal)
~/.edtime-sync/run-edtime.sh fetch week=current

# Pipeline lengkap: fetch → process → export Cursor
~/.edtime-sync/run-edtime.sh sync full

# Cek export
~/.edtime-sync/run-edtime.sh status
```

---

## Langkah 7 — Cursor iOS / Cursor Mac baca data

### Opsi A — Google Drive MCP (disarankan)

1. Copy MCP config:

```bash
mkdir -p ~/.cursor
cp edtime-sync-hub/cursor/mcp.json.example ~/.cursor/mcp.json
```

2. Restart Cursor → authenticate Google Drive
3. Minta agent: *"Baca Edtime Sync/cursor/latest.json dan ringkas jadwal minggu ini"*

### Opsi B — Sheet tab CursorExportRows

Buka Google Sheet → tab `CursorExportRows` → copy ke Cursor chat.

### Opsi C — Web App JSON

```bash
curl "$(security find-generic-password -s edtime-sync -a webhook-url -w)?action=cursor-edtime-export"
```

---

## Perintah run-edtime.sh

| Perintah | Fungsi |
|----------|--------|
| `open` | Dispatch buka edtime di iPhone |
| `fetch [week=current]` | Dispatch fetch SS + jadwal |
| `sync full` | Pipeline lengkap |
| `process` | Proses inbox Drive + merge Sheet |
| `export` | Buat `latest.json` untuk Cursor |
| `status` | Ringkasan export |
| `credentials webhook <url>` | Simpan webhook Keychain |

---

## Alur SS (Screenshot) otomatis

Karena iOS **tidak bisa** screenshot app lain sepenuhnya otomatis:

1. Shortcut **buka edtime**
2. **Notifikasi**: "Screenshot Schichtplan sekarang"
3. Anda **1 tap** Vol Up + Side Button
4. Shortcut **ambil foto terbaru** dari album Screenshots
5. **Simpan** ke `iCloud Drive/Edtime Sync/Screenshots/`
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
- [`AGENTIC-MONITOR-GUIDE.md`](AGENTIC-MONITOR-GUIDE.md)
- [`../iphone/EDTIME-SHORTCUTS-SETUP.md`](../iphone/EDTIME-SHORTCUTS-SETUP.md)
