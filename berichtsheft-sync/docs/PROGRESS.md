# Progress Berichtsheft-Sync

Terakhir diperbarui: 5 Juni 2026 — persiapan upload GitHub + dokumentasi lengkap.

## Checklist

| Item | Status | Catatan |
|------|--------|---------|
| Telegram + `.env` token | ✅ **Selesai** | Bot aktif, user ID dibatasi via `.env` |
| Keychain BLok | ✅ **Selesai** | `credentials set --service blok` |
| DB + jadwal + generator | ✅ | `init`, `import` JSON EdTime |
| Bot `/log` `/selesai` `/ok` `/ubah` | ✅ | Teks biasa = log |
| Dry-run BLok (HTML) | ✅ | `output/blok_dry_run/` |
| Terjemahan ID→DE (kamus) | ✅ | `translate_de.py` |
| **Gemini polish (Fase A)** | ✅ **Siap** | Butuh `GEMINI_API_KEY` di `.env` |
| **Gemini Vision** | ✅ | Foto EdTime, kegiatan, berufsschule |
| `config.yaml` + selector BLok | ✅ **Selesai** | Format Woche, selector Wicket |
| **Worker `--live`** | ✅ **Selesai** | `live_blok_after_finish: true` |
| BLok audit `/minggu` `/audit` | ✅ | Scan gap mingguan |
| Upload lampiran BLok | ✅ | `/lampirkan` → Dokumentenablage |
| Cursor SDK `/ai` | ✅ | Opsional, butuh `CURSOR_API_KEY` |
| WiFi portal auto | ❌ Opsional | `wifi.*` di `config.yaml` |
| Submit otomatis L2 penuh | 🟡 Sebagian | `/ok` isi live; submit minggu manual |
| Dokumentasi GitHub | ✅ | README, LANDASAN, TECH_STACK, GITHUB_UPLOAD |
| Katalog kegiatan per Abteilung | ✅ | `data/katalog_abteilung.json` + CLI `catalog` |

## Yang sudah berjalan end-to-end

1. Import jadwal → `python3 -m berichtsheft import data/shifts_*.json`
2. Log via Telegram (teks/foto) → tersimpan di SQLite
3. `/selesai` → orchestrator + worker (dry-run atau live)
4. `/ok` → approve + isi BLok live (jika `require_ok_before_submit`)
5. `/minggu` / `/audit` → deteksi gap di BLok

## Yang masih opsional / perlu penyesuaian

| Item | Tindakan |
|------|----------|
| Selector BLok berubah | Update `config.yaml` setelah inspect F12 |
| WiFi portal kantor | Isi `wifi.*` di `config.yaml` |
| Gemini API key | Tambah di `.env` untuk polish & Vision |
| Submit minggu otomatis | Belum diaktifkan penuh (L2) |

## AI / Cursor

| | |
|--|--|
| **Gemini** | Opsional — polish teks + Vision foto. Lihat `docs/GEMINI.md` |
| **Cursor** | `/ai` via SDK — pengembangan & konsultasi, bukan runtime harian |

## Hari libur (contoh Ausgang)

Jadwal `Frei`/`Ausgang` → `/selesai` → "Hari libur — tidak diisi BLok".  
`/ubah` tidak bisa pada hari libur. Pakai tanggal **hari kerja** atau update jadwal.

## Uji cepat

```bash
python3 -m berichtsheft test-flow
python3 -m unittest discover -s tests -v
```

## Langkah berikutnya (pasca-GitHub)

1. `gh auth login` → `gh repo create berichtsheft-sync --push` (lihat `docs/GITHUB_UPLOAD.md`)
2. Rotasi token jika pernah ter-commit `.env` secara tidak sengaja
3. Uji live 1 hari kerja: `worker --date YYYY-MM-DD --live`
