"""Set dropdown BLok: presence, Lernort, Abteilung — dari EdTime."""

from __future__ import annotations

import sqlite3
from typing import Any

from berichtsheft.blok_mapping import abteilung_for_shift, load_blok_mapping

WEEKDAY_EN = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def resolve_day_fields(
    shift: sqlite3.Row | dict[str, Any],
    day_idx: int,
    mapping: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Hitung nilai presence, location, abteilung tanpa Playwright (unit-testable).
    Weekend arbeit: Wochenende → Anwesend supaya textarea tersedia.
    """
    mapping = mapping or load_blok_mapping()
    day_type = shift["day_type"] if isinstance(shift, sqlite3.Row) else shift.get("day_type")
    applied: dict[str, Any] = {"day_type": day_type}

    if day_type == "frei":
        pres = (mapping.get("presence") or {}).get("frei", "Abwesend")
        applied["presence"] = pres
        return applied

    pres_map = mapping.get("presence") or {}
    loc_map = mapping.get("location") or {}
    presence = pres_map.get(day_type, "Anwesend")
    if day_idx >= 5 and day_type == "arbeit":
        presence = mapping.get("weekend_arbeit_presence", "Anwesend")
    location = loc_map.get(day_type, "Ausbildungsbetrieb")

    applied["presence"] = presence
    applied["location"] = location

    shift_dict = dict(shift) if isinstance(shift, sqlite3.Row) else shift
    abt = abteilung_for_shift(mapping, shift_dict)
    if abt:
        applied["abteilung"] = abt

    return applied


def _select_by_label(page, selector: str, label: str) -> bool:
    loc = page.locator(selector)
    if not loc.count() or not label:
        return False
    try:
        loc.first.select_option(label=label)
        loc.first.dispatch_event("change")
        page.wait_for_timeout(400)
        return True
    except Exception:
        return False


def apply_day_fields(
    page,
    day_en: str,
    day_idx: int,
    shift: sqlite3.Row | dict[str, Any],
    mapping: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Terapkan presence + location (+ abteilung minggu) sesuai EdTime.
    Weekend arbeit: Wochenende → Anwesend supaya textarea tersedia.
    """
    mapping = mapping or load_blok_mapping()
    resolved = resolve_day_fields(shift, day_idx, mapping)
    applied = dict(resolved)

    if resolved.get("day_type") == "frei":
        _select_by_label(
            page,
            f'select[name="tableComp:{day_en}:trspaceplus:presence"]',
            resolved["presence"],
        )
        return applied

    _select_by_label(
        page,
        f'select[name="tableComp:{day_en}:trspaceplus:presence"]',
        resolved["presence"],
    )
    _select_by_label(
        page,
        f'select[name="tableComp:{day_en}:trspaceplus:location"]',
        resolved["location"],
    )

    abt = resolved.get("abteilung")
    if abt:
        dep = page.locator('select[name="department:dep:dep"]')
        if dep.count():
            _select_by_label(page, 'select[name="department:dep:dep"]', abt)
        else:
            inp = page.locator('input[name="department:dep:dep"]')
            if inp.count():
                inp.first.fill(abt)
                inp.first.dispatch_event("change")

    page.wait_for_timeout(300)
    return applied
