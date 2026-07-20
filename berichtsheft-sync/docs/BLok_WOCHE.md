# BLok — format Woche (dari screenshot Anda)

## Yang terlihat di layar Anda

| Item | Nilai |
|------|--------|
| Tab aktif | **Woche** (bukan Tag) |
| Format | **Wochenbericht** — 1 kotak teks per hari |
| Hari kerja | Mo–Fr: Ausbildungsbetrieb / Anwesend |
| Weekend | Sa–So: Wochenende |
| Jam | `0h:00min` per hari (field terpisah) |
| User | Agwen |

Sistem sudah diset: `config.yaml` → `format: woche`

## Cara isi otomatis (konsep)

Untuk tanggal **2026-06-05 (Freitag)**:

- Index hari = **4** (Mo=0, Di=1, Mi=2, Do=3, **Fr=4**)
- Worker isi **textarea ke-5** di halaman minggu itu
- Jam: dikonversi ke format `8h:30min` (dari shift EdTime)

**Penting:** Anda harus buka **minggu yang benar** di BLok (KW yang sama dengan tanggal draft).

## F12 — yang perlu dicek (opsional perbaikan)

1. Di halaman Woche, F12 → klik textarea **Jumat**
2. Copy selector → bandingkan dengan `day_textareas: 'textarea'`
3. Klik field **0h:00min** Jumat → Copy selector → `day_hours` jika `input[type="text"]` terlalu umum

## Uji

```bash
python3 -m berichtsheft finish --date 2026-06-06 --fill
python3 -m berichtsheft worker --date 2026-06-06 --live
```

Buka minggu **KW 23** (01.–07.06.2026) di BLok sebelum/saat worker jalan.

## Weekend — ikut EdTime

Sabtu/Minggu **boleh diisi** jika EdTime punya shift (contoh **06–07.06 BRF**).  
Hanya **Ausgang** yang di-skip — bukan karena hari Sabtu/Minggu.
