"""Load EdTime → BLok field mapping."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from berichtsheft.config_loader import ROOT

MAPPING_PATH = ROOT / "data" / "blok_mapping.yaml"


def load_blok_mapping() -> dict[str, Any]:
    if not MAPPING_PATH.exists():
        return {}
    return yaml.safe_load(MAPPING_PATH.read_text(encoding="utf-8")) or {}


def abteilung_for_shift(mapping: dict[str, Any], shift: dict[str, Any]) -> str:
    abt = mapping.get("abteilung") or {}
    tags = shift.get("tags") or []
    if not tags and shift.get("tags_json"):
        try:
            tags = json.loads(shift["tags_json"])
        except (json.JSONDecodeError, TypeError):
            tags = []
    if isinstance(tags, str):
        tags = [tags]
    for tag in tags:
        key = str(tag).strip()
        if key in abt:
            return abt[key]
    day_type = shift.get("day_type")
    if day_type == "schule":
        return abt.get("Schule") or abt.get("default") or ""
    return abt.get("default") or ""
