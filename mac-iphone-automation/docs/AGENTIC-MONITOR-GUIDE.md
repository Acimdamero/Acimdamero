# Panduan Monitor-Only — edtime Agentic Setup

Anda **tidak perlu** mengetik perintah setup manual. Agent menjalankan semuanya. Peran Anda: **isi secrets sekali → monitor → putuskan → test**.

---

## Satu perintah di Mac

```bash
cd mac-iphone-automation
cp config/secrets.example.env ~/.automation-hub/secrets.env
# Edit 2 baris wajib: GOOGLE_SHEET_ID + HUB_WEBHOOK_URL
bash run-edtime-agentic.sh
```

Setelah itu agent otomatis:

1. Install Hub + edtime scripts  
2. Simpan webhook & sheet ID ke Keychain/config  
3. Panggil Apps Script `?action=setup-edtime` (buat tab Sheet)  
4. Aktifkan daemon (poll queue + sync jam 07:00 & 19:00)  
5. Dispatch `edtime-fetch` ke iPhone  
6. Process + export `latest.json` untuk Cursor  
7. Tulis laporan + daftar keputusan Anda  

---

## Monitor (Anda hanya lihat ini)

```bash
# Dashboard sekali
~/.automation-hub/scripts/edtime-monitor.sh status

# Live refresh 30 detik
~/.automation-hub/scripts/edtime-monitor.sh watch
```

### File laporan

| File | Isi |
|------|-----|
| `~/.automation-hub/edtime/agent-report.json` | Status agent terakhir |
| `~/.automation-hub/edtime/pending-decisions.json` | **Yang hanya Anda bisa lakukan** |
| `Drive/Edtime/cursor/latest.json` | Data untuk Cursor |
| `~/.automation-hub/logs/edtime-schedule.log` | Log sync terjadwal |

---

## Keputusan yang HANYA Anda (tidak bisa agent)

| # | Keputusan | Kapan |
|---|-----------|-------|
| 1 | Deploy Apps Script + paste URL ke `secrets.env` | Sekali |
| 2 | Buat Shortcut iPhone (EDTIME-SHORTCUTS-SETUP.md) | Sekali (~15 menit) |
| 3 | Login edtime di iPhone | Sekali |
| 4 | Tap SS Schichtplan saat fetch | Setiap sync (1 tap) |
| 5 | Review `latest.json` di Cursor | Sebelum pakai data |

Agent **tidak bisa** Face ID, Shortcuts di iPhone, atau deploy Google tanpa OAuth browser Anda.

---

## Test (Anda)

```bash
bash test-edtime-pipeline.sh
~/.automation-hub/run-task.sh edtime-sync full
~/.automation-hub/run-task.sh edtime-status
```

Di Cursor: *"Baca Automation Hub/Edtime/cursor/latest.json"*

---

## Jadwal otomatis

LaunchAgent `com.automation.edtime-sync` jalan **07:00** dan **19:00** setiap hari.

Matikan: `launchctl unload ~/Library/LaunchAgents/com.automation.edtime-sync.plist`

---

## Troubleshooting agent

| Gejala | Perbaikan otomatis | Anda |
|--------|-------------------|------|
| webhook ❌ | `edtime-agent-orchestrator.sh configure` | Redeploy Apps Script |
| fetch timeout | Agent lanjut process data ada | Unlock iPhone + SS |
| export kosong | Mock test lulus? | Isi jadwal via fetch |
| daemon tidak jalan | `launchctl load ...edtime-sync.plist` | Restart Mac |

---

## Arsitektur agentic

```
run-edtime-agentic.sh
    └── edtime-agent-orchestrator.sh
            ├── install (hub + edtime)
            ├── configure (secrets → Keychain)
            ├── autostart (LaunchAgents)
            ├── sync (dispatch → wait → process → export)
            └── pending-decisions.json → edtime-monitor.sh
```

Anda di loop: **monitor → test → approve data di Cursor**.
