# Tab Google Sheet — edtime Sync

Tambahkan tab berikut di Spreadsheet **Automation Queue** (selain `Queue`).

---

## Tab: `EdtimeSchedule`

Data jadwal normalisasi dari iPhone / Mac.

| Kolom | Contoh |
|-------|--------|
| id | a1b2c3d4 |
| date | 2026-07-11 |
| start_time | 08:00 |
| end_time | 16:30 |
| shift_code | SpV |
| break_minutes | 30 |
| location | Station A |
| status | planned / worked |
| raw_source | iphone / web / manual |
| synced_at | ISO timestamp |
| notes | |

---

## Tab: `EdtimeRaw`

Payload mentah (debug / OCR / form iPhone).

| timestamp | device | payload_type | payload_json |

---

## Tab: `EdtimeScreenshots`

Metadata screenshot (file di Google Drive).

| timestamp | device | screen_type | filename | drive_path | notes |

`screen_type`: `schichtplan` | `stundenzettel` | `dashboard`

---

## Tab: `EdtimeSession`

Log status login edtime.

| timestamp | device | status | extra |

Status: `logged_in` | `needs_login` | `fetch_ok` | `fetch_error`

---

## Tab: `CursorExport`

Ringkasan export untuk Cursor.

| exported_at | record_count | json_summary |

---

## Tab: `CursorExportRows` (auto-generated)

Dibuat otomatis oleh `EdtimeWebApp.gs` — baris datar untuk Cursor baca.

| date | start_time | end_time | shift_code | break_minutes | hours_worked | location | status | source | berichtsheft_template |

---

## Apps Script

1. Paste `EdtimeWebApp.gs` saja (standalone — tanpa WhatsApp/WAHA)
2. Deploy Web App → salin URL ke Mac:

```bash
bash setup-edtime-sync.sh
# atau:
~/.edtime-sync/scripts/edtime-save-credentials.sh webhook 'YOUR_WEB_APP_URL'
```

---

## Endpoint API (Web App)

| Method | URL | Fungsi |
|--------|-----|--------|
| GET | `?action=cursor-edtime-export` | JSON bundle untuk Cursor |
| GET | `?action=edtime-schedule` | Alias schedule export |
| GET | `?device=iphone` | Poll antrian Queue |
| POST | `{"action":"edtime_schedule","schedule":[...]}` | Tulis jadwal |
| POST | `{"action":"edtime_session","status":"logged_in"}` | Log session |
| POST | `{"action":"edtime_screenshot",...}` | Log screenshot metadata |
| POST | `{"action":"edtime_cursor_export","payload":{...}}` | Update export |
