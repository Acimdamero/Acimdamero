# EdTime → BLok (bukan Mo–Fr otomatis)

## Prinsip

| Sumber kebenaran | **EdTime** (import JSON), bukan hari kalender |
|------------------|-----------------------------------------------|
| **Ausgang** | Tidak isi BLok |
| **Schule** | Isi BLok — Ort: Berufsschule |
| **Arbeit** (BRF, HK, Tagung, BAF, …) | Isi BLok — Ort: Betrieb |
| **Sabtu / Minggu** | **Boleh kerja** jika EdTime ada shift (contoh 06–07.06 BRF) |

## Contoh dari jadwal Anda

### KW 22 (Mei)
| Tanggal | EdTime | BLok |
|---------|--------|------|
| 25–26 Mo–Di | Ausgang | Skip |
| 27–29 Mi–Fr | Schule | Isi (Schule) |
| 30 Sa | Ausgang | Skip |
| **31 So** | **BAF 08:00–16:30** + HK | **Isi** (bukan Wochenende kosong) |

### KW 23 (Juni)
| Tanggal | EdTime | BLok |
|---------|--------|------|
| 01 Mo | BRF | Isi |
| 02–03 | Ausgang | Skip |
| 04 Do | FS2 / Tagung | Isi |
| 05 Fr | BRF + HK | Isi |
| **06 Sa** | BRF + HK | **Isi** |
| **07 So** | BRF | **Isi** |

### KW 24
| 08–12 Mo–Fr | Schule | Isi |

## Import jadwal

```bash
cd ~/Projects/berichtsheft-sync
python3 -m berichtsheft import data/shifts_edtime_kw22_24.json
```

## BLok halaman „Woche“

- **7 kotak** = Mo … So (index 0–6)
- Worker isi **kotak hari yang sama** dengan tanggal draft
- **So 31.05** = index **6**, bukan „weekend skip“

Buka **minggu kalender yang benar** di BLok (KW 22 / 23 / 24) sebelum `worker --live`.

## Update mingguan

1. Screenshot EdTime → edit JSON (atau kirim ke Cursor untuk dibantu)
2. `python3 -m berichtsheft import data/shifts_….json`
3. Operasi harian: `/log` → `/selesai` → `worker --live`
