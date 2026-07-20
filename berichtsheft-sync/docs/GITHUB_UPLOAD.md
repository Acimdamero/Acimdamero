# Panduan Upload ke GitHub

Langkah demi langkah untuk mengunggah proyek **Berichtsheft-Sync** ke akun GitHub Anda.

---

## Sebelum upload — cek keamanan

Pastikan file berikut **tidak** akan ter-commit:

| File | Alasan |
|------|--------|
| `.env` | Token Telegram, API key Gemini/Cursor |
| `berichtsheft.db` | Data pribadi: log, draft, shift |
| `config.yaml` | Konfigurasi lokal (salin dari `config.example.yaml`) |
| `data/telegram_chat_id.txt` | Chat ID pribadi |
| `data/attachments/` | Foto pribadi |
| `output/` | Screenshot dry-run |

Verifikasi:

```bash
cd ~/Projects/berichtsheft-sync
git status
# .env dan berichtsheft.db TIDAK boleh muncul
```

Jika `.env` muncul, pastikan `.gitignore` berisi baris `.env`.

---

## Opsi A — GitHub CLI (`gh`) — disarankan

### A.1 Instalasi gh (jika belum ada)

```bash
brew install gh
gh auth login
# Pilih: GitHub.com → HTTPS → Login via browser
```

### A.2 Buat repo dan push

```bash
cd ~/Projects/berichtsheft-sync

# Pastikan di branch main
git branch -M main

# Buat repo publik (atau --private untuk privat)
gh repo create berichtsheft-sync \
  --public \
  --source=. \
  --remote=origin \
  --description "Otomatisasi Berichtsheft Hotelfachmann Azubi via Telegram + BLok" \
  --push
```

### A.3 Jika repo sudah ada di GitHub

```bash
git remote add origin git@github.com:USERNAME/berichtsheft-sync.git
git push -u origin main
```

Ganti `USERNAME` dengan username GitHub Anda.

---

## Opsi B — Manual (tanpa gh CLI)

### B.1 Buat repository di web

1. Buka [https://github.com/new](https://github.com/new)
2. **Repository name:** `berichtsheft-sync`
3. **Description:** Otomatisasi Berichtsheft Hotelfachmann Azubi via Telegram + BLok
4. Pilih **Public** atau **Private**
5. **Jangan** centang "Add a README" (sudah ada lokal)
6. Klik **Create repository**

### B.2 Push dari terminal

```bash
cd ~/Projects/berichtsheft-sync
git branch -M main
git remote add origin git@github.com:USERNAME/berichtsheft-sync.git
git push -u origin main
```

Atau dengan HTTPS:

```bash
git remote add origin https://github.com/USERNAME/berichtsheft-sync.git
git push -u origin main
```

---

## Setelah upload — setup di mesin baru

```bash
git clone git@github.com:USERNAME/berichtsheft-sync.git
cd berichtsheft-sync

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env          # isi token
cp config.example.yaml config.yaml

python3 -m berichtsheft init
python3 -m berichtsheft credentials set --service blok
```

---

## Commit berikutnya

```bash
git add -A
git status   # cek tidak ada .env
git commit -m "feat: deskripsi perubahan"
git push
```

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `gh: command not found` | `brew install gh` |
| `Permission denied (publickey)` | Setup SSH key: `ssh-keygen` + tambah ke GitHub Settings → SSH |
| `.env` ter-commit | `git rm --cached .env` lalu commit ulang; rotasi token |
| `remote origin already exists` | `git remote set-url origin git@github.com:USER/berichtsheft-sync.git` |
| Repo terlalu besar | Pastikan `node_modules/` dan `output/` di `.gitignore` |

---

## Rekomendasi visibility

| Tipe | Kapan |
|------|-------|
| **Private** | Default — berisi alur kerja pribadi Azubi |
| **Public** | Jika ingin berbagi sebagai template open-source (tanpa data pribadi) |

Untuk repo **public**, pastikan tidak ada data shift nyata di `data/shifts_*.json` yang bisa diidentifikasi.
