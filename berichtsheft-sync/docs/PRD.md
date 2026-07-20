# PRD — Berichtsheft-Sync v1.0

## 1. Ringkasan

Sistem semi-otomatis untuk **Hotelfachmann**: laporan kegiatan via **Telegram (HP)** → orkestrator + DB → **isi BLok di web** → Azubi cek **~5 menit** (`OK` / ubah).

EdTime: **upload manual** (screenshot/JSON). Cursor: **pengembangan & konsultasi**, bukan runtime harian.

## 2. Tujuan

| Metrik | Target |
|--------|--------|
| Waktu admin Berichtsheft | ≤ 5 menit/hari (cek + approve) |
| Input saat kerja | ≤ 30 detik per catatan (bot) |
| Akurasi | Berdasarkan log user + shift, bukan tebakan |

## 3. Persona

- **Azubi:** input HP, approve malam.
- **Robot (Mac):** login BLok, isi form.
- **Ausbilder:** tetap di BLok resmi (di luar scope v1).

## 4. Alur utama

1. **Mingguan:** upload jadwal (`import` JSON dari EdTime).
2. **Saat kerja:** `/log …` (beberapa kali).
3. **Selesai kerja:** `/selesai` (+ ringkasan opsional).
4. **Sistem:** orchestrate → draft DE → worker isi BLok (L1).
5. **Azubi:** preview Telegram → `/ok` atau `/ubah …`.
6. **Opsional L2:** submit minggu setelah OK.

## 5. Functional requirements

| ID | Requirement |
|----|-------------|
| F1 | Simpan kredensial BLok di Keychain (Mac) |
| F2 | Telegram: log, selesai, status, ok, ubah |
| F3 | DB: shifts, work_logs, areas, drafts, approvals |
| F4 | Orchestrator: gabung log + template + shift |
| F5 | Worker BLok: dry-run dan live mode |
| F6 | WiFi helper: deteksi SSID + klik portal (config) |
| F7 | Multi-bahasa input; output DE ke BLok |

## 6. Non-functional

- Password tidak di git / Cursor chat / log AI.
- Hari `frei` tidak diisi BLok.
- Worker gagal → notifikasi Telegram.

## 7. Out of scope v1

- EdTime API (tidak ada untuk Azubi).
- Automasi tanpa `/selesai` atau tanpa log.
- Submit Kammer / PDF Prüfung.

## 8. Fase delivery

| Fase | Deliverable | Status |
|------|-------------|--------|
| 1 | PRD, SETUP, DB, generator | Done |
| 2 | Keychain, orchestrator, work logs | In progress |
| 3 | API + Telegram bot | In progress |
| 4 | BLok worker dry-run | In progress |
| 5 | WiFi helper config | In progress |
| 6 | Uji coba simulasi | In progress |

## 9. Konfigurasi

Lihat `config.example.yaml` dan `docs/SETUP.md`.
