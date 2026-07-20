# Landasan Proyek — Berichtsheft-Sync

## Latar belakang

Sebagai **Azubi Hotelfachmann** di Jerman, Anda wajib mengisi **Berichtsheft** (laporan kegiatan pelatihan) secara rutin melalui platform **BLok** (*online-ausbildungsnachweis.de*). Proses manual memakan waktu:

- Mencari kembali apa yang dikerjakan di shift
- Menulis ulang dalam bahasa Jerman formal
- Mengisi form web per hari/minggu
- Melampirkan foto dokumentasi ke *Entwicklungsportfolio*

Sementara itu, jadwal kerja sudah ada di **EdTime**, dan catatan singkat lebih mudah diketik dari **HP** saat istirahat.

## Masalah yang dipecahkan

| Masalah | Dampak |
|---------|--------|
| Input ganda (EdTime + BLok) | Waktu admin 15–30 menit/hari |
| Menulis Jerman saat lelah | Kualitas teks tidak konsisten |
| Lupa isi hari tertentu | Gap di BLok, teguran Ausbilder |
| Portal WiFi kantor | Mac offline, worker gagal |
| Kredensial tersebar | Risiko kebocoran password |

## Tujuan proyek

1. **Input cepat dari HP** — Telegram bot, teks Indonesia atau Jerman, foto dengan Vision
2. **Otomatisasi pengisian BLok** — Worker Playwright mengisi form setelah `/selesai`
3. **Kontrol Azubi** — Preview + `/ok` sebelum submit resmi (~5 menit/hari)
4. **Keamanan** — Password BLok di Keychain macOS, bukan di repo atau chat AI
5. **Audit proaktif** — `/minggu` dan `/audit` mendeteksi minggu kosong

## Ruang lingkup (in scope)

- Import jadwal shift dari **JSON EdTime** (manual export/screenshot→Vision)
- Log aktivitas harian via Telegram
- Generator draft dari template `Hotelfachmann` + shift + log user
- Terjemahan Indonesia → Jerman (kamus + opsional Gemini polish)
- Worker BLok format **Woche** (1 textarea per hari kerja)
- Upload lampiran ke BLok *Dokumentenablage*
- Dry-run HTML untuk verifikasi sebelum live
- Reminder otomatis jika ada gap

## Di luar ruang lingkup (v1)

| Item | Alasan |
|------|--------|
| EdTime API resmi | Tidak tersedia untuk Azubi |
| Submit otomatis ke Kammer | Butuh persetujuan Ausbilder manual |
| VPS cloud headless | Keychain khusus macOS; IP asing bisa diblokir BLok |
| Automasi tanpa `/selesai` | Azubi harus mengonfirmasi aktivitas |
| Hari libur (`Frei`/`Ausgang`) | Tidak diisi ke BLok (sesuai aturan) |

## Prinsip desain

1. **Azubi di pusat** — Sistem membantu menulis, bukan mengarang aktivitas
2. **Template terbatas** — Generator hanya memakai pool `templates_hotelfach.json`
3. **Transparansi** — Dry-run HTML + preview Telegram sebelum live
4. **Fail-safe** — Worker gagal → notifikasi Telegram, tidak submit diam-diam
5. **Satu mesin robot** — MacBook sebagai stasiun (API + worker + Keychain)

## Persona

| Peran | Peran dalam sistem |
|-------|-------------------|
| **Azubi (Anda)** | Input HP, approve `/ok`, import jadwal |
| **MacBook** | API server, bot polling, worker BLok, Keychain |
| **Ausbilder** | Review di BLok resmi (di luar sistem) |
| **BLok** | Platform target pengisian Berichtsheft |

## Metrik sukses

| Metrik | Target |
|--------|--------|
| Waktu admin Berichtsheft | ≤ 5 menit/hari |
| Input saat kerja | ≤ 30 detik per catatan |
| Akurasi isi | Berdasarkan log user + shift, bukan tebakan AI |
| Gap mingguan | Terdeteksi sebelum Ausbilder |

## Referensi terkait

- [PRD.md](PRD.md) — requirement fungsional detail
- [ARCHITECTURE.md](ARCHITECTURE.md) — diagram komponen
- [SETUP.md](SETUP.md) — panduan instalasi
