# BLok Fase 2 — Otomasi penuh

## Yang diotomatisasi

| Fitur | Modul | Keterangan |
|-------|--------|------------|
| Presence libur/masuk | `blok_fields.py` | Weekend + `arbeit` → Anwesend (bukan Wochenende) |
| Abteilung per hari | `blok_fields.py` + `data/blok_mapping.yaml` | Tag EdTime → dropdown `department:dep:dep` |
| Lernort | `blok_fields.py` | `schule` → Berufsschule, `arbeit` → Ausbildungsbetrieb |
| Navigasi minggu | `blok_nav.py` | `weekBefore`/`weekAfter` + fallback **Jahresansicht** |
| Live fill | `blok_worker.py` | Login → navigasi → fields → textarea → jam → simpan |
| Audit laporan lama | `blok_audit.py` | Agustus 2025 – sekarang, klik navigasi (bukan `goto` href) |
| Status minggu | `blok_status.py` | bearbeitbar / freigegeben / abgenommen |

## Alur harian

```bash
# 1. Log kerja (Telegram atau CLI)
python3 -m berichtsheft log --text "BRF pagi"

# 2. Orchestrator + dry-run
python3 -m berichtsheft finish --date 2026-06-05 --fill

# 3. Live BLok (butuh Keychain + Playwright)
python3 -m berichtsheft worker --date 2026-06-05 --live
```

Atau satu perintah:

```bash
python3 -m berichtsheft finish --date 2026-06-05 --fill --live
```

## Config (`config.yaml`)

```yaml
blok:
  format: woche
  auto_save: true

orchestrator:
  auto_fill_blok_after_finish: true
  live_blok_after_finish: false   # true = Telegram /selesai langsung isi BLok
  require_ok_before_submit: true  # true = live fill baru setelah /ok
```

## Mapping EdTime → BLok

Edit `data/blok_mapping.yaml` jika nama dropdown BLok berbeda.

## Audit penuh

```bash
python3 -m berichtsheft audit --from 2025-08-01 --to 2026-06-05
```

Output: `output/blok_audit/report.json`

- Minggu **bearbeitbar**: baca textarea, jam, presence, location dari form.
- Minggu **abgenommen**: parse teks read-only dari body (tanpa textarea).

## Batasan: minggu abgenommen

Minggu yang sudah **abgenommen** (ditandatangani Ausbilder) **tidak diisi otomatis**.

- Worker mendeteksi status di halaman Woche.
- Jika `abgenommen` tanpa **Bearbeitungsmodus** / `editmodeCheck`: `live_fill` gagal dengan pesan jelas.
- Jika Bearbeitungsmodus tersedia: worker mencoba isi (risiko ditolak server — uji manual dulu).
- **Jangan** memaksa edit minggu terkunci; ubah manual di BLok atau minta Ausbilder buka kembali.

## Telegram + live

1. Set `live_blok_after_finish: true` di `config.yaml`.
2. `/selesai` → isi BLok sungguhan (jika minggu bearbeitbar).
3. Atau `require_ok_before_submit: true` + live → `/ok` memicu worker live.

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Weekend tanpa textarea | Pastikan `weekend_arbeit_presence: Anwesend` di mapping; shift EdTime `arbeit` |
| Navigasi gagal | Cek login; worker coba Jahresansicht otomatis |
| Abgenommen | Lihat batasan di atas |
| Selector salah | `scripts/blok_probe.py`, sesuaikan `config.yaml` |
