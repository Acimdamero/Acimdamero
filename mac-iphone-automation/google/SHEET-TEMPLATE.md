# Template Google Sheet — Automation Queue

Buat Spreadsheet baru di [Google Sheets](https://sheets.google.com) dengan nama **Automation Queue**.

## Tab: `Queue`

| A (id) | B (device) | C (command) | D (status) | E (args) |
|--------|------------|-------------|------------|----------|
| 001 | mac | status | pending | |
| 002 | mac | backup | done | all |
| 003 | iphone | notify | pending | Backup selesai |

### Nilai `device`

- `mac` — dieksekusi di Mac (daemon atau SSH)
- `iphone` — dieksekusi di iPhone (Shortcuts polling)

### Perintah Mac (`run-task.sh`)

| command | args contoh | Keterangan |
|---------|-------------|------------|
| status | | Info disk, uptime, battery |
| backup | all / documents / desktop | rsync ke Google Drive |
| open-app | Safari | Buka app |
| quit-app | Spotify | Tutup app |
| sleep | | Tidurkan Mac |
| wake | | Bangunkan layar |
| cursor-pull | ~/Developer/my-app | Git pull |
| cursor-build | ~/Developer/my-app | npm/pnpm build |

### Perintah iPhone (Shortcuts)

| command | args | Keterangan |
|---------|------|------------|
| notify | Teks notifikasi | Show Notification |
| open-url | https://... | Buka URL |
| focus-on | Do Not Disturb | Focus mode (jika didukung) |
| run-shortcut | Nama Shortcut | Jalankan shortcut lain |

## Folder Google Drive

Buat struktur:

```
Automation Hub/
├── Backups/     ← backup Mac
├── Logs/        ← log status JSON
└── Config/      ← export config (tanpa secret)
```

## Setup Apps Script

1. Di Spreadsheet: **Extensions → Apps Script**
2. Paste isi `apps-script/QueueSync.gs`
3. **Deploy → New deployment → Web app**
4. Execute as: **Me** | Who has access: **Anyone** (atau hanya Anda)
5. Salin **Web App URL** → masukkan ke Shortcuts iPhone

## Sheet ID

Dari URL spreadsheet:
`https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`

Salin `SHEET_ID_HERE` ke `~/.automation-hub/config.env`:

```
GOOGLE_SHEET_ID=SHEET_ID_HERE
```
