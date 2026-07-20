# Dua komputer — PC kantor + MacBook (tanpa ganggu jaringan admin)

## Masalah

| Mesin | Peran | Terhubung ke DB Berichtsheft? |
|-------|--------|-------------------------------|
| **PC kantor + Cursor Cloud** | Edit kode / katalog kegiatan | **Tidak** — dan **tidak perlu** |
| **MacBook (rumah / pribadi)** | Stasiun robot: SQLite, Telegram bot, Playwright BLok, Keychain | **Ya** — satu-satunya |

Anda **tidak** perlu menyambungkan PC kantor ke MacBook, VPN, Tailscale, atau port-forward. Itu yang ribet dan bisa menyentuh kebijakan IT.

---

## Prinsip (supaya tidak ribet)

1. **Yang diedit di kantor = file teks di GitHub** (katalog kegiatan), bukan file `berichtsheft.db`.
2. **Database runtime** (shift, log Telegram, draft, approval) **hanya hidup di MacBook**.
3. **Sinkron = `git push` / `git pull`** lewat internet biasa (GitHub) — sama seperti update dokumen, bukan trafik admin lokal.
4. **Jangan** jalankan `serve`, `bot`, atau `worker --live` di PC kantor.

```
[PC kantor / Cursor Cloud]
        │  edit data/katalog_abteilung.json
        ▼
    [GitHub]  ←── satu-satunya jembatan
        │  git pull + catalog --reload
        ▼
[MacBook: SQLite + bot + BLok + Keychain]
        ▲
[iPhone Telegram] ── operasi harian ──┘
```

---

## Di PC kantor (Cursor) — hanya ini

### Boleh
- Edit `data/katalog_abteilung.json` (kegiatan per Abteilung)
- Edit template teks, keywords, mapping
- Commit + push ke GitHub
- Baca `docs/KATALOG_KEGIATAN.md`

### Jangan
- `credentials set` / simpan password BLok
- `serve` + `bot` (Telegram polling)
- `worker --live` (login BLok)
- Copy `berichtsheft.db` / `.env` ke USB atau share kantor
- VPN / remote desktop ke Mac hanya demi edit katalog

### Alur 2 menit

```bash
# di salinan repo (folder berichtsheft-sync atau clone resmi)
# 1) edit data/katalog_abteilung.json
# 2) commit & push
git add data/katalog_abteilung.json docs/KATALOG_KEGIATAN.md
git commit -m "update katalog: …"
git push
```

Kalau mau regenerasi docs di tempat yang ada Python:

```bash
python3 -m berichtsheft catalog --write-md
```

`--reload` **tidak wajib** di kantor (tidak ada DB produksi di sini).

---

## Di MacBook — terima update katalog

Sekali setelah Anda push dari kantor (bisa malam / weekend):

```bash
cd ~/Projects/berichtsheft-sync
git pull
./scripts/sync_katalog_from_git.sh
# atau manual:
# python3 -m berichtsheft catalog --reload --write-md
```

Ini hanya mengisi ulang **template + area** di SQLite lokal.  
**Tidak** menghapus work_logs / drafts / approvals / shifts yang sudah ada (reload katalog hanya ganti tabel template & areas).

Operasi harian tetap di Mac:

```bash
python3 -m berichtsheft serve   # terminal 1
python3 -m berichtsheft bot     # terminal 2
```

---

## Apa yang sinkron vs tidak

| Data | Sinkron lewat GitHub? | Di mana “benar”? |
|------|------------------------|------------------|
| Katalog kegiatan / Abteilung | **Ya** (`katalog_abteilung.json`) | Git → lalu Mac reload |
| Jadwal contoh JSON | Boleh (file di `data/`) | Git → Mac `import` |
| SQLite runtime (`berichtsheft.db`) | **Tidak** | Hanya MacBook |
| `.env` (Telegram, Gemini) | **Tidak** | Hanya MacBook |
| Password BLok (Keychain) | **Tidak** | Hanya MacBook |
| Log / draft / approval harian | **Tidak** | Hanya MacBook |

---

## Kenapa ini aman untuk jaringan kantor

- Tidak membuka port di LAN kantor
- Tidak remote ke MacBook dari kantor
- Tidak login BLok dari IP/kantor perusahaan
- Trafik keluar hanya ke **GitHub** (HTTPS) seperti kerja kode biasa
- Administrator tidak perlu izin khusus untuk “jembatan ke laptop pribadi”

---

## Kalau nanti ingin edit jadwal dari kantor

Tetap pola sama: edit file JSON shift → push → di Mac `import`:

```bash
# Mac
git pull
python3 -m berichtsheft import data/shifts_….json
```

Jangan coba “share database” antar PC.

---

## Checklist singkat

| Saat | Di mana | Tindakan |
|------|---------|----------|
| Istirahat kantor, mau ubah teks BRF/HK | Cursor di PC kantor | Edit JSON → commit → push |
| Pulang / buka Mac | MacBook | `git pull` + `./scripts/sync_katalog_from_git.sh` |
| Shift kerja | HP + Mac online | `/log` → `/selesai` → `/ok` seperti biasa |
| PC kantor | — | Tidak menjalankan bot/BLok |
