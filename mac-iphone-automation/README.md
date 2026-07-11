# Mac ↔ iPhone Automation Hub

Pusat otomatisasi untuk **Mac**, **iPhone**, **Google (Drive/Sheets)**, dan **Cursor** — backup file, kontrol aplikasi, dan workflow coding dari satu antrian perintah.

## Apa yang bisa dilakukan

| Area | Fitur |
|------|--------|
| **Backup** | rsync Documents/Desktop/Downloads → Google Drive |
| **Kontrol Mac** | Sleep, wake, buka/tutup app — dari iPhone via SSH |
| **Kontrol iPhone** | Mac tulis perintah ke Google Sheet → iPhone eksekusi via Shortcuts |
| **Cursor** | Git pull + build project dari iPhone atau agent Cursor |
| **edtime sync** | Fetch jadwal iPhone (SS) → Sheet/Drive → export JSON untuk Cursor |
| **Akun** | 1Password CLI + Apple Keychain (tanpa password di file teks) |

## Struktur proyek

```
mac-iphone-automation/
├── mac/              # Script Mac + installer + daemon
├── iphone/           # Panduan Shortcuts + command registry
├── google/           # Template Sheet + Apps Script + tab mapping
├── cursor/           # Contoh MCP config
├── config/           # Contoh environment
└── docs/             # Arsitektur iPhone + akun & keamanan
```

## Dokumentasi arsitektur iPhone

**Peta lengkap kontrol & integrasi iPhone:**

- [`docs/SETUP-EDTIME-SYNC.md`](docs/SETUP-EDTIME-SYNC.md) — **setup edtime auto-sync → Cursor (SS + Sheet + Drive)**
- [`docs/EDTIME-BERICHTSHEFT-ARCHITECTURE.md`](docs/EDTIME-BERICHTSHEFT-ARCHITECTURE.md) — **skema jembatan edtime (iPhone) ↔ Berichtsheft**, batasan, pro/kontra
- [`docs/IPHONE-ARCHITECTURE-MAP.md`](docs/IPHONE-ARCHITECTURE-MAP.md) — lapisan, matriks kontrol, trigger, sync topology
- [`docs/PERMISSIONS-AND-WORKAROUNDS.md`](docs/PERMISSIONS-AND-WORKAROUNDS.md) — **cara izinkan akses & workaround otomatisasi**
- [`docs/WAHA-API-GUIDE.md`](docs/WAHA-API-GUIDE.md) — **WAHA self-hosted API (akali WA personal)**
- [`iphone/command-registry.json`](iphone/command-registry.json) — registry perintah machine-readable
- [`google/SHEET-TABS-MAP.md`](google/SHEET-TABS-MAP.md) — tab Devices, Inventory, Triggers

## Quick start (Mac)

```bash
git clone https://github.com/Acimdamero/Acimdamero.git
cd Acimdamero/mac-iphone-automation
bash setup-wizard.sh    # wizard interaktif (izin + SSH + Sheet)
# atau manual:
bash mac/install.sh
```

Edit `~/.automation-hub/config.env`:

```bash
GOOGLE_SHEET_ID=your_sheet_id_from_google_sheets_url
```

Test:

```bash
~/.automation-hub/run-task.sh status
~/.automation-hub/run-task.sh backup all
```

## Quick start (Google)

1. Buat Spreadsheet **Automation Queue** — lihat [`google/SHEET-TEMPLATE.md`](google/SHEET-TEMPLATE.md)
2. Pasang Apps Script — [`google/apps-script/QueueSync.gs`](google/apps-script/QueueSync.gs)
3. Buat folder Drive `Automation Hub/Backups`

## Quick start (edtime → Cursor)

```bash
bash setup-edtime-sync.sh          # wizard: Keychain, Drive, Sheet tabs
# iPhone: iphone/EDTIME-SHORTCUTS-SETUP.md

~/.automation-hub/run-task.sh edtime-sync full
~/.automation-hub/run-task.sh edtime-export
# Cursor baca: Drive/Automation Hub/Edtime/cursor/latest.json
```

Panduan lengkap: [`docs/SETUP-EDTIME-SYNC.md`](docs/SETUP-EDTIME-SYNC.md)

**Agentic (Anda hanya monitor):** [`docs/AGENTIC-MONITOR-GUIDE.md`](docs/AGENTIC-MONITOR-GUIDE.md)

```bash
cp config/secrets.example.env ~/.automation-hub/secrets.env
# isi GOOGLE_SHEET_ID + HUB_WEBHOOK_URL
bash run-edtime-agentic.sh
bash mac/scripts/edtime-monitor.sh watch
```

## Quick start (iPhone)

Ikuti [`iphone/SHORTCUTS-GUIDE.md`](iphone/SHORTCUTS-GUIDE.md):

- SSH ke Mac (Status, Backup, Sleep, App control)
- Polling antrian iPhone dari Google Sheet

**WhatsApp (terbatas iOS):** [`iphone/WHATSAPP-GUIDE.md`](iphone/WHATSAPP-GUIDE.md) — buka chat, prefill pesan, template; **tidak bisa** baca inbox atau auto-send penuh.

**WhatsApp personal GRATIS + auto kirim:** [`docs/WHATSAPP-PERSONAL-GRATIS.md`](docs/WHATSAPP-PERSONAL-GRATIS.md) — WAHA self-host, biaya Rp 0.

## Quick start (Cursor)

1. Gemini API → Cursor Settings → Models → Google → Verify
2. Copy MCP config:

```bash
mkdir -p ~/.cursor
cp cursor/mcp.json.example ~/.cursor/mcp.json
```

3. Restart Cursor → authenticate Google Drive MCP

## Arsitektur

```
iPhone (Shortcuts + SSH) ──► Mac Agent (run-task.sh)
                                    │
Google Sheet (antrian) ◄────────────┤
                                    ▼
                            Google Drive (backup/log)
                                    ▲
                            Cursor MCP (AI agent)
```

## Perintah tersedia

```bash
run-task.sh status
run-task.sh backup all|documents|desktop
run-task.sh open-app Safari
run-task.sh quit-app Spotify
run-task.sh sleep|wake
run-task.sh cursor-pull ~/Developer/my-app
run-task.sh cursor-build ~/Developer/my-app
run-task.sh queue-process
run-task.sh edtime-sync full
run-task.sh edtime-export
run-task.sh edtime-fetch week=current
```

## Keamanan

- Remote Login Mac + SSH key (bukan password)
- Token Google di 1Password atau Keychain — lihat [`docs/ACCOUNTS.md`](docs/ACCOUNTS.md)
- iOS tidak mengizinkan kontrol penuh semua app — otomatisasi per Shortcuts yang Anda definisikan

## Batasan Apple

Kontrol **100% semua app/sistem iPhone** tidak didukung oleh Apple. Hub ini memberikan **framework maksimal** yang aman dan legal: antrian pusat + SSH Mac + Shortcuts iPhone + integrasi Google/Cursor.

---

Dibuat untuk otomatisasi bertahap — mulai dari backup & status, lalu tambah perintah custom di Sheet dan Shortcuts.
