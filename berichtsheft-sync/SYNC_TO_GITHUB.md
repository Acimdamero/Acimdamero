# Sync perubahan katalog ke repo GitHub standalone

Repo resmi: https://github.com/Acimdamero/berichtsheft-sync

Environment Cloud Agent saat ini hanya punya akses tulis ke `Acimdamero/Acimdamero`.
Salinan kerja ada di folder ini; patch siap-terapkan:

- `/berichtsheft-sync-katalog.patch` (di root profil)

```bash
cd ~/Projects/berichtsheft-sync   # clone resmi
git checkout -b cursor/katalog-abteilung-data-5f8c
git apply /path/to/Acimdamero/berichtsheft-sync-katalog.patch
# atau salin file dari folder berichtsheft-sync/ di repo profil
git add -A && git commit -m "feat: katalog kegiatan per Abteilung"
git push -u origin HEAD
```

Setelah edit kegiatan sehari-hari, cukup ubah:

`data/katalog_abteilung.json`

lalu:

```bash
python3 -m berichtsheft catalog --reload --write-md
```
