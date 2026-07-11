# Deploy Webhook — Sheet ID Anda

**Spreadsheet:** Automation Queue  
**GOOGLE_SHEET_ID:** `1so9zekw-afSOueqYLNpSl-gfStJc8FsyOknW3QDt5pM`

---

## Step 1 — Paste `secrets.env` di Mac (copy exact)

```bash
nano ~/.automation-hub/secrets.env
```

```bash
GOOGLE_SHEET_ID=1so9zekw-afSOueqYLNpSl-gfStJc8FsyOknW3QDt5pM
HUB_WEBHOOK_URL=
AUTONOMOUS=1
SKIP_WAHA=1
EDTIME_AUTO_SYNC=1
```

Simpan: `Ctrl+O` → Enter → `Ctrl+X`

---

## Step 2 — Deploy Apps Script (5 menit)

1. Buka spreadsheet:  
   https://docs.google.com/spreadsheets/d/1so9zekw-afSOueqYLNpSl-gfStJc8FsyOknW3QDt5pM/edit

2. **Extensions → Apps Script**

3. Hapus isi `Code.gs` default

4. **Copy seluruh isi file:**  
   `google/apps-script/AutomationHub-WebApp.gs`  
   (satu file — sudah include Queue + edtime + stub WhatsApp)

5. Paste → **Save** (Ctrl+S)

6. **Deploy → New deployment**
   - Type: **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**

7. **Authorize** jika diminta → Copy **Web app URL**

8. Edit secrets.env — isi baris kosong:

```bash
HUB_WEBHOOK_URL=https://script.google.com/macros/s/AKfycb.../exec
```

Atau via terminal:

```bash
~/.automation-hub/scripts/edtime-save-credentials.sh webhook 'PASTE_URL_DISINI'
```

---

## Step 3 — Test webhook

```bash
curl "https://script.google.com/macros/s/.../exec?device=iphone"
curl "https://script.google.com/macros/s/.../exec?action=cursor-edtime-export"
curl "https://script.google.com/macros/s/.../exec?action=setup-edtime"
```

Harus return **JSON** (bukan HTML error).

---

## Step 4 — Jalankan agent Mac

```bash
cd ~/Acimdamero/mac-iphone-automation   # sesuaikan path clone
git pull
bash run-edtime-agentic.sh
```

Monitor:

```bash
~/.automation-hub/scripts/edtime-monitor.sh watch
```

---

## Status checklist

| Item | Status |
|------|--------|
| Google Sheet 11 tabs | ✅ Done (Gemini) |
| GOOGLE_SHEET_ID | ✅ `1so9zekw-afSOueqYLNpSl-gfStJc8FsyOknW3QDt5pM` |
| Apps Script deploy | ⬜ Anda — Step 2 |
| HUB_WEBHOOK_URL | ⬜ Setelah deploy |
| secrets.env | ⬜ Step 1 + webhook |
| run-edtime-agentic.sh | ⬜ Step 4 |
| iPhone Shortcuts | ⬜ EDTIME-SHORTCUTS-SETUP.md |

---

## Context untuk Cursor (paste ke chat)

```
Sheet ready: Automation Queue
GOOGLE_SHEET_ID=1so9zekw-afSOueqYLNpSl-gfStJc8FsyOknW3QDt5pM
Tabs: Queue, EdtimeSchedule, EdtimeRaw, EdtimeScreenshots, EdtimeSession,
      CursorExport, CursorExportRows, Devices, Inventory, Triggers, README
Next: deploy AutomationHub-WebApp.gs → HUB_WEBHOOK_URL → run-edtime-agentic.sh
Repo: mac-iphone-automation/ branch cursor/mac-iphone-automation-hub-8703
```
