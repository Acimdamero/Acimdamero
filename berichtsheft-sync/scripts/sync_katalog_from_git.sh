#!/usr/bin/env bash
# Jalankan di MacBook setelah git pull — muat ulang katalog ke SQLite lokal.
# Tidak menyentuh work_logs, drafts, approvals, atau shifts.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f data/katalog_abteilung.json ]]; then
  echo "Tidak ada data/katalog_abteilung.json — pastikan Anda di folder berichtsheft-sync." >&2
  exit 1
fi

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "→ git status (opsional cek)"
git status -sb || true

echo "→ reload katalog ke SQLite + sync docs"
python3 -m berichtsheft catalog --reload --write-md

echo "✓ Selesai. Cek ringkas:"
python3 -m berichtsheft catalog --abteilung Service | head -25
echo "…"
echo "DB runtime tetap di: $(python3 -c 'from berichtsheft import db; print(db.DEFAULT_DB)')"
