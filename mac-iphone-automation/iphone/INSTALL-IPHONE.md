# Instalasi iPhone — Automation Hub

Jalankan **setelah** Mac `bash install-all.sh` selesai.

---

## Step 1: SSH Key dari Mac

Di Mac Terminal, jalankan:
```bash
cat ~/.ssh/automation_hub.pub
```
Copy output → paste di iPhone Shortcuts (SSH Key field).

Hostname Mac (dari wizard):
```bash
scutil --get LocalHostName
# Contoh: MacBook-Pro.local
```

---

## Step 2: Buat 3 Shortcut

### A — Hub — Status Mac
| Field | Value |
|-------|-------|
| Action | Run Script Over SSH |
| Host | `MacBook-Pro.local` |
| User | username Mac |
| Auth | SSH Key (paste dari Step 1) |
| Script | `~/.automation-hub/run-task.sh status` |

### B — Hub — WhatsApp Test (via Mac)
| Field | Value |
|-------|-------|
| Action | Run Script Over SSH |
| Script | `~/.automation-hub/run-task.sh waha-send-name "agwen acim damero jerman" "Test dari iPhone Hub"` |

### C — Hub — Notify Test
| Field | Value |
|-------|-------|
| Action | Show Notification |
| Title | Hub Test |
| Body | iPhone automation aktif |

---

## Step 3: Pin ke Home Screen

Tap shortcut → Share → **Add to Home Screen**

---

## Step 4: Automation (opsional)

Automation → Time of Day → every hour  
→ Run **Hub — Notify Test**  
→ **Ask Before Running: OFF**

---

## Test urutan

1. ▶ **Hub — Status Mac** → lihat JSON status
2. ▶ **Hub — WhatsApp Test** → pesan terkirim ke kontak (Mac + WAHA harus hidup)
3. **Hub — Notify Test** → notifikasi muncul

---

## Jika SSH gagal

- Mac & iPhone **Wi-Fi sama**
- Remote Login **ON** di Mac
- Hostname benar (`xxx.local`)

## Jika WA gagal

- Docker Desktop **running** di Mac
- http://localhost:3000 **bisa dibuka di Mac**
- QR WhatsApp **sudah di-scan**
