# Setup Shortcuts iPhone — edtime Sync

Ikuti langkah ini di **iPhone** setelah `setup-edtime-sync.sh` di Mac selesai.

---

## 0. Simpan Webhook URL di iPhone

1. Copy Web App URL dari Mac setup
2. **Notes** atau **Files** → buat note `HubWebhookURL`
3. Atau di Shortcuts: buat **Text** action dengan URL → gunakan di semua shortcut edtime

---

## 1. Shortcut: Hub — edtime Login Assist

Spec: [`edtime-login-assist.shortcut-spec.json`](edtime-login-assist.shortcut-spec.json)

1. Shortcuts → **+** → nama: **Hub — edtime Login Assist**
2. **Open App** → edtime Mitarbeiter-App
3. **Wait** 3 detik
4. **Find Passwords** → search "edtime" (iOS 18+)
5. **If** Password found:
   - Copy username → **Show Notification** "Paste username"
   - Copy password → **Show Notification** "Tap Login + Face ID"
6. **Else**: **Show Alert** "Simpan password di Settings → Passwords"
7. **Get Contents of URL** POST:

```json
{"action":"edtime_session","device":"iphone","status":"login_assist_shown"}
```

---

## 2. Shortcut: Hub — edtime Fetch (SS + sync)

Spec: [`edtime-fetch.shortcut-spec.json`](edtime-fetch.shortcut-spec.json)

### Alur singkat

1. **Open App** edtime
2. **Wait** 4 detik
3. **Show Notification**: "Screenshot Schichtplan (Vol Up + Side)"
4. **Wait** 8 detik
5. **Find Photos** → Album Screenshots → 5 menit terakhir → 1 foto
6. **Save File** → iCloud Drive/`Edtime Sync/Screenshots/`
7. **Ask for Input** tanggal + jam shift (semi-auto: bisa paste dari clipboard)
8. **POST** ke webhook:

```json
{
  "action": "edtime_schedule",
  "device": "iphone",
  "schedule": [{
    "date": "2026-07-11",
    "start_time": "08:00",
    "end_time": "16:30",
    "shift_code": "SpV",
    "raw_source": "iphone_ss"
  }]
}
```

9. **POST** screenshot metadata + session `fetch_ok`
10. **Show Notification** "edtime sync OK"

### Parse jam dari input "08:00-16:30"

Tambah action **Match Text** dengan regex `(\d{2}:\d{2})-(\d{2}:\d{2})` → split ke start/end.

---

## 3. Update Hub — Execute Command

Tambahkan **If** blocks:

| command | Aksi |
|---------|------|
| `edtime-open` | Open App edtime |
| `edtime-fetch` | Run Shortcut **Hub — edtime Fetch** |
| `edtime-login` | Run Shortcut **Hub — edtime Login Assist** |

Input format dari Sheet: `edtime-fetch|week=current`

---

## 4. Update Hub — Process iPhone Queue

Di loop **Repeat Each** pending command, tambah handler di atas sebelum `markDone`.

Contoh mark done — **Get Contents of URL**:

```
POST {WEBHOOK}?markDone=1&row={row_number}
```

Atau update Sheet manual via Apps Script `markDone(row)`.

---

## 5. Automation

**Personal Automation → Time of Day → every 15 min**

- Run **Hub — Process iPhone Queue**
- **Run Immediately**: ON

**Opsional — Charger connected:**

- Run **Hub — edtime Fetch** (malam hari, HP unlocked)

---

## 6. Login edtime — first time

1. Buka edtime → login dengan akun employer
2. ✅ Centang tetap login jika ada
3. Settings iPhone → Passwords → Add → `edtime.de` + kredensial
4. Test: **Hub — edtime Login Assist** (simulasi session expired)

---

## 7. Test dari iPhone

1. Jalankan manual **Hub — edtime Fetch**
2. SS Schichtplan saat diminta
3. Isi jam shift
4. Cek Google Sheet tab `EdtimeSchedule`
5. Di Mac: `run-edtime.sh export`

---

## Batasan SS di iOS

| Bisa | Tidak bisa |
|------|------------|
| Buka edtime otomatis | SS tanpa tap user |
| Ambil foto SS terbaru dari album | Baca teks di dalam edtime native |
| Upload ke iCloud Drive | Auto-fill login tanpa Face ID |

Untuk akurasi lebih tinggi: login **web edtime** di Safari iPhone → export → drop ke Drive inbox.
