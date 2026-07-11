# Prompt Gemini Pro — Setup Spreadsheet Automation Queue

Copy-paste prompt di bawah ke **Gemini di Google Sheets** (side panel) pada spreadsheet kosong atau baru.

---

## PROMPT 1 — Buat semua tab & struktur (copy mulai sini)

```
Kamu adalah asisten setup Google Spreadsheet untuk proyek otomasi "edtime-sync-hub" + sinkronisasi app edtime ke Cursor AI.

TUGAS: Di spreadsheet INI, buat struktur lengkap berikut. Jangan tanya konfirmasi — langsung eksekusi semua langkah yang bisa kamu lakukan di Sheets.

═══════════════════════════════════════
A. INFORMASI SPREADSHEET
═══════════════════════════════════════
- Rename file/spreadsheet menjadi: Automation Queue
- Buat semua tab di bawah (hapus atau rename Sheet1 default jadi Queue)

═══════════════════════════════════════
B. TAB 1: Queue (PENTING — antrian perintah)
═══════════════════════════════════════
Header baris 1 (kolom A–E):
id | device | command | status | args

Baris contoh (baris 2–6):
001 | mac | status | pending |
002 | mac | backup | done | all
003 | iphone | notify | pending | Automation Hub aktif
004 | iphone | edtime-fetch | pending | week=current
005 | mac | edtime-sync | pending | full

Freeze baris 1. Bold header. Kolom lebar: A=100, B=80, C=150, D=80, E=200

Catatan untuk tab README di cell G1 (merge G1:J8):
device = mac (eksekusi di Mac) atau iphone (eksekusi di iPhone Shortcuts)
status = pending | done | failed
command edtime: edtime-open, edtime-fetch, edtime-sync, berichtsheft-sync

═══════════════════════════════════════
C. TAB 2: EdtimeSchedule
═══════════════════════════════════════
Header:
id | date | start_time | end_time | shift_code | break_minutes | location | status | raw_source | synced_at | notes

Freeze row 1. Format kolom date sebagai YYYY-MM-DD.

═══════════════════════════════════════
D. TAB 3: EdtimeRaw
═══════════════════════════════════════
Header:
timestamp | device | payload_type | payload_json

═══════════════════════════════════════
E. TAB 4: EdtimeScreenshots
═══════════════════════════════════════
Header:
timestamp | device | screen_type | filename | drive_path | notes

Contoh screen_type: schichtplan, stundenzettel, dashboard

═══════════════════════════════════════
F. TAB 5: EdtimeSession
═══════════════════════════════════════
Header:
timestamp | device | status | extra

Status valid: logged_in, needs_login, fetch_ok, fetch_error, login_assist_shown

═══════════════════════════════════════
G. TAB 6: CursorExport
═══════════════════════════════════════
Header:
exported_at | record_count | json_summary

═══════════════════════════════════════
H. TAB 7: CursorExportRows
═══════════════════════════════════════
Header:
date | start_time | end_time | shift_code | break_minutes | hours_worked | location | status | source | berichtsheft_template

═══════════════════════════════════════
I. TAB 8: Devices
═══════════════════════════════════════
Header:
timestamp | device | battery | wifi | hostname | extra

Baris contoh:
2026-07-11T12:00:00Z | mac | AC | HomeWiFi | MacBook-Pro | setup ok

═══════════════════════════════════════
J. TAB 9: Inventory
═══════════════════════════════════════
Header:
app | category | shortcuts_actions | automatable | hub_command | notes

Isi baris contoh:
edtime Mitarbeiter-App | Work | Open App, manual SS | partial | edtime-fetch | Jadwal kerja
Shortcuts | System | Run Shortcut | yes | run-shortcut |
Safari | Browser | Open URL | yes | open-url |

═══════════════════════════════════════
K. TAB 10: Triggers
═══════════════════════════════════════
Header:
name | trigger_type | condition | shortcut | run_immediately | enabled

Isi baris:
Poll Queue | Time of Day | Every 15 min | Hub — Process iPhone Queue | yes | yes
edtime Fetch | Time of Day | 07:00 and 19:00 | Hub — edtime Fetch | yes | yes
Home Status | Wi-Fi | Home SSID | Hub — Post iPhone Status | yes | yes

═══════════════════════════════════════
L. TAB 11: README
═══════════════════════════════════════
Buat tab README dengan panduan singkat:

1. GOOGLE_SHEET_ID = ambil dari URL browser antara /d/ dan /edit
2. Deploy Apps Script: Extensions → Apps Script → paste EdtimeWebApp.gs → Deploy Web App
3. HUB_WEBHOOK_URL = URL Web App yang di-deploy
4. Mac: isi ~/.edtime-sync/secrets.env lalu bash run-agent.sh

═══════════════════════════════════════
M. FORMATTING
═══════════════════════════════════════
- Semua tab: header baris 1 = bold, background abu-abu terang (#f3f3f3)
- Freeze row 1 di setiap tab
- Urutan tab: Queue, EdtimeSchedule, EdtimeRaw, EdtimeScreenshots, EdtimeSession, CursorExport, CursorExportRows, Devices, Inventory, Triggers, README
- Tab Queue = tab aktif default

═══════════════════════════════════════
N. OUTPUT AKHIR (wajib tulis di chat setelah selesai)
═══════════════════════════════════════
Setelah selesai, balas dengan format EXACT:

---HASIL SETUP---
SPREADSHEET_NAME: Automation Queue
TAB_COUNT: [jumlah tab]
GOOGLE_SHEET_ID: [tulis ID spreadsheet ini — string panjang dari URL, BUKAN URL lengkap]
CHECKLIST:
- [ ] Queue header OK
- [ ] Edtime tabs OK
- [ ] Sample rows OK
LANGKAH MANUAL USER:
1. Copy GOOGLE_SHEET_ID ke Mac secrets.env
2. Extensions → Apps Script → deploy Web App
3. Paste HUB_WEBHOOK_URL ke secrets.env
---SELESAI---
```

---

## PROMPT 2 — Ambil GOOGLE_SHEET_ID saja (jika sheet sudah ada)

```
Spreadsheet ini dipakai untuk **edtime-sync-hub**. Tolong:

1. Tulis GOOGLE_SHEET_ID spreadsheet ini (ID dari URL, antara /d/ dan /edit)
2. Cek tab "Queue" punya header: id, device, command, status, args
3. Jika belum lengkap, perbaiki sesuai struktur Automation Queue
4. Output format:

GOOGLE_SHEET_ID=xxxxxxxx

Tanpa URL lengkap, hanya ID-nya saja.
```

---

## PROMPT 3 — Apps Script (di Gemini Apps Script / atau manual)

Gemini di Sheets **tidak bisa deploy Web App** otomatis. Setelah Prompt 1 selesai, lakukan manual:

1. **Extensions → Apps Script**
2. Paste 1 file dari repo `edtime-sync-hub`:
   - `google/apps-script/EdtimeWebApp.gs`
3. **Deploy → New deployment → Web app**
   - Execute as: Me
   - Who has access: Anyone
4. Copy URL → `HUB_WEBHOOK_URL` di Mac

Prompt untuk Gemini **di Apps Script editor** (opsional):

```
Buat project Apps Script untuk spreadsheet Automation Queue dengan:
- doGet: poll antrian device=iphone/mac, export ?action=cursor-edtime-export, setup ?action=setup-edtime
- doPost: terima edtime_schedule, edtime_session, edtime_screenshot, append Queue
- Fungsi setupEdtimeTabs yang buat semua tab edtime jika belum ada

Jangan pakai library eksternal. Compatible Google Apps Script V8.
```

(Lebih aman: paste file .gs asli dari repo — sudah ditest.)

---

## Setelah Gemini selesai — isi secrets.env di Mac

```bash
GOOGLE_SHEET_ID=<dari output Gemini>
HUB_WEBHOOK_URL=<setelah deploy Apps Script>
AUTONOMOUS=1
SKIP_WAHA=1
```

```bash
bash run-agent.sh
```
