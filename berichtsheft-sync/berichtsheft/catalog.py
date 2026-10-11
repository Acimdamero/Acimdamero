"""Katalog kegiatan per Abteilung — load, tampil, sync ke SQLite & file sample."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from berichtsheft import db

ROOT = Path(__file__).resolve().parent.parent
KATALOG_PATH = ROOT / "data" / "katalog_abteilung.json"
AREAS_PATH = ROOT / "data" / "areas_hotel.json"
TEMPLATES_PATH = ROOT / "data" / "templates_hotelfach.json"
MAPPING_PATH = ROOT / "data" / "blok_mapping.yaml"
DOCS_PATH = ROOT / "docs" / "KATALOG_KEGIATAN.md"

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DAY_TYPES = frozenset({"arbeit", "schule", "frei"})
_WEEKDAYS = frozenset({"mo", "di", "mi", "do", "fr", "sa", "so"})
_TIME_BANDS = frozenset({"frueh", "spaet", "nacht", "any"})


def load_katalog(path: Path | None = None) -> dict[str, Any]:
    path = path or KATALOG_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def save_katalog(data: dict[str, Any], path: Path | None = None) -> Path:
    """Persist katalog JSON (pretty-printed). Caller should sync_to_db afterwards."""
    path = path or KATALOG_PATH
    validate_katalog(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def validate_katalog(data: dict[str, Any]) -> None:
    """Reject a malformed katalog. Missing ``conditions`` stays valid."""
    if not isinstance(data, dict):
        raise ValueError("katalog must be a JSON object")
    abteilungen = data.get("abteilungen")
    if not isinstance(abteilungen, list):
        raise ValueError("katalog harus punya key 'abteilungen' (list)")
    for abt in abteilungen:
        if not isinstance(abt, dict):
            raise ValueError("setiap Abteilung harus object")
        for item in abt.get("codes") or []:
            if not isinstance(item, dict):
                raise ValueError("setiap code harus object")
            code = str(item.get("code") or "?")
            if "conditions" not in item or item.get("conditions") is None:
                continue
            conds = item["conditions"]
            if not isinstance(conds, list):
                raise ValueError(f"{code}: conditions harus array")
            seen: set[str] = set()
            for cond in conds:
                _validate_condition(code, cond, seen)


def _validate_condition(code: str, cond: Any, seen: set[str]) -> None:
    if not isinstance(cond, dict):
        raise ValueError(f"{code}: condition harus object")
    cid = cond.get("id")
    if not isinstance(cid, str) or not _SLUG.match(cid):
        raise ValueError(f"{code}: condition id harus slug (contoh check-in-rush)")
    if cid in seen:
        raise ValueError(f"{code}: condition id duplikat: {cid}")
    seen.add(cid)
    label = cond.get("label_de")
    if not isinstance(label, str) or not label.strip():
        raise ValueError(f"{code}/{cid}: label_de wajib")
    when = cond.get("when")
    if not isinstance(when, dict):
        raise ValueError(f"{code}/{cid}: when harus object")
    _check_choice(code, cid, when, "day_type", _DAY_TYPES)
    _check_choice(code, cid, when, "weekday", _WEEKDAYS)
    _check_choice(code, cid, when, "time_band", _TIME_BANDS)
    for key in ("guest_situation", "tags"):
        if key not in when or when[key] is None:
            continue
        val = when[key]
        if not isinstance(val, list) or not all(
            isinstance(x, str) and x.strip() for x in val
        ):
            raise ValueError(f"{code}/{cid}: when.{key} harus array string")
    texts = cond.get("texts_de")
    if not isinstance(texts, list) or not 2 <= len(texts) <= 4:
        raise ValueError(f"{code}/{cid}: texts_de harus 2–4 kalimat")
    if not all(isinstance(t, str) and t.strip() for t in texts):
        raise ValueError(f"{code}/{cid}: texts_de harus string non-kosong")


def _check_choice(
    code: str,
    cid: str,
    when: dict[str, Any],
    key: str,
    allowed: frozenset[str],
) -> None:
    if key not in when or when[key] is None:
        return
    if when[key] not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"{code}/{cid}: when.{key} harus salah satu dari {choices} atau null")


def format_when(when: dict[str, Any] | None) -> str:
    """Compact matcher line for CLI text and markdown."""
    when = when or {}
    parts = [
        f"day_type={when.get('day_type') or 'any'}",
        f"weekday={when.get('weekday') or 'any'}",
        f"time_band={when.get('time_band') or 'any'}",
    ]
    guests = when.get("guest_situation") or []
    tags = when.get("tags") or []
    if guests:
        parts.append("guest_situation=" + ", ".join(guests))
    if tags:
        parts.append("tags=" + ", ".join(tags))
    return ", ".join(parts)


def iter_codes(katalog: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Flat list of code entries with parent abteilung metadata."""
    katalog = katalog or load_katalog()
    rows: list[dict[str, Any]] = []
    for abt in katalog.get("abteilungen", []):
        blok_name = abt.get("blok_name") or ""
        skip = bool(abt.get("skip_blok"))
        for code_item in abt.get("codes", []):
            rows.append(
                {
                    "blok_name": blok_name,
                    "skip_blok": skip,
                    "description_de": abt.get("description_de"),
                    **code_item,
                }
            )
    return rows


def sync_to_db(conn: sqlite3.Connection, katalog: dict[str, Any] | None = None) -> dict[str, int]:
    """Load katalog into activity_templates + work_areas.

    ``templates_de`` stays the default generator pool. ``conditions`` are stored
    on ``work_areas.conditions_json`` (file remains source of truth) and are not
    mixed into ``activity_templates``.
    """
    katalog = katalog or load_katalog()
    validate_katalog(katalog)
    db.init_schema(conn)
    conn.execute("DELETE FROM activity_templates")
    conn.execute("DELETE FROM work_areas")

    templates = 0
    areas = 0
    conditions = 0
    for item in iter_codes(katalog):
        code = item["code"]
        department = item.get("department")
        lernfeld = item.get("lernfeld")
        item_conditions = item.get("conditions") or []
        conditions += len(item_conditions)
        for text in item.get("templates_de") or []:
            db.upsert_template(conn, code, department, lernfeld, text)
            templates += 1
        # aliases share the same template texts for generator lookups
        for alias in item.get("aliases") or []:
            for text in item.get("templates_de") or []:
                db.upsert_template(conn, alias, department, lernfeld, text)
                templates += 1

        db.upsert_area(
            conn,
            code,
            item.get("name_de", code),
            item.get("keywords") or [],
            item.get("default_activities_de") or [],
            item_conditions,
        )
        areas += 1
        for alias in item.get("aliases") or []:
            db.upsert_area(
                conn,
                alias,
                item.get("name_de", alias),
                item.get("keywords") or [],
                item.get("default_activities_de") or [],
                item_conditions,
            )
            areas += 1

    conn.commit()
    return {"templates": templates, "areas": areas, "conditions": conditions}


def export_legacy_files(katalog: dict[str, Any] | None = None) -> None:
    """Keep areas_hotel.json + templates_hotelfach.json in sync for older docs."""
    katalog = katalog or load_katalog()
    areas_out: list[dict[str, Any]] = []
    templates_out: list[dict[str, Any]] = []

    for item in iter_codes(katalog):
        areas_out.append(
            {
                "code": item["code"],
                "name_de": item.get("name_de", item["code"]),
                "keywords": item.get("keywords") or [],
                "default_activities_de": item.get("default_activities_de") or [],
            }
        )
        templates_out.append(
            {
                "code": item["code"],
                "department": item.get("department"),
                "lernfeld": item.get("lernfeld"),
                "texts": item.get("templates_de") or [],
            }
        )

    AREAS_PATH.write_text(
        json.dumps({"areas": areas_out}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    TEMPLATES_PATH.write_text(
        json.dumps({"templates": templates_out}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def format_catalog_text(katalog: dict[str, Any] | None = None) -> str:
    katalog = katalog or load_katalog()
    lines: list[str] = [
        "Katalog kegiatan per Abteilung",
        "=" * 40,
        katalog.get("note", ""),
        "",
    ]
    for abt in katalog.get("abteilungen", []):
        blok = abt.get("blok_name") or "(tanpa Abteilung / skip BLok)"
        lines.append(f"## Abteilung BLok: {blok}")
        if abt.get("description_de"):
            lines.append(f"   {abt['description_de']}")
        if abt.get("skip_blok"):
            lines.append("   ⚠ skip_blok = true")
        lines.append("")
        for item in abt.get("codes", []):
            aliases = item.get("aliases") or []
            alias_s = f" (alias: {', '.join(aliases)})" if aliases else ""
            lines.append(f"  • Code: {item['code']}{alias_s}")
            lines.append(f"    Nama: {item.get('name_de', '')}")
            lines.append(f"    Department: {item.get('department', '')}")
            lines.append(f"    Lernfeld: {item.get('lernfeld') or '-'}")
            kw = ", ".join(item.get("keywords") or [])
            lines.append(f"    Keywords: {kw or '-'}")
            defaults = item.get("default_activities_de") or []
            if defaults:
                lines.append("    Default:")
                for d in defaults:
                    lines.append(f"      - {d}")
            texts = item.get("templates_de") or []
            lines.append(f"    Templates ({len(texts)}):")
            for i, t in enumerate(texts, 1):
                lines.append(f"      {i}. {t}")
            conds = item.get("conditions") or []
            lines.append(f"    Conditions ({len(conds)}):")
            for cond in conds:
                lines.append(f"      [{cond.get('id')}] {cond.get('label_de', '')}")
                lines.append(f"        when: {format_when(cond.get('when'))}")
                for i, t in enumerate(cond.get("texts_de") or [], 1):
                    lines.append(f"        {i}. {t}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_catalog_markdown(katalog: dict[str, Any] | None = None) -> str:
    katalog = katalog or load_katalog()
    lines: list[str] = [
        "# Katalog kegiatan per Abteilung",
        "",
        "> File sumber (edit di sini): [`data/katalog_abteilung.json`](../data/katalog_abteilung.json)",
        "",
        katalog.get("note", ""),
        "",
        "Setelah edit JSON:",
        "",
        "```bash",
        "python3 -m berichtsheft catalog --reload",
        "python3 -m berichtsheft catalog --write-md   # regenerasi file ini",
        "```",
        "",
        "## Conditions bearbeiten",
        "",
        "Conditions (variabel situasi) diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) pada array `conditions` setiap code. Field `templates_de` tetap pool default dan tetap kompatibel dengan generator yang ada.",
        "",
        "Matcher `when` (semua opsional, `null` = any):",
        "",
        "| Key | Nilai |",
        "|-----|--------|",
        "| day_type | `arbeit`, `schule`, `frei`, atau `null` |",
        "| weekday | `mo`, `di`, `mi`, `do`, `fr`, `sa`, `so`, atau `null` |",
        "| time_band | `frueh`, `spaet`, `nacht`, `any` |",
        "| guest_situation | array tag situasi tamu |",
        "| tags | array tag tugas |",
        "",
        "Setiap condition punya `id` (slug), `label_de`, `when`, dan `texts_de` (2–4 kalimat Jerman). Generator nanti memilih teks dari condition yang `when`-nya cocok; sampai saat itu `templates_de` tetap sumber kalimat default.",
        "",
    ]
    for abt in katalog.get("abteilungen", []):
        blok = abt.get("blok_name") or "(tanpa Abteilung / skip BLok)"
        lines.append(f"## {blok or 'Frei / skip'}")
        lines.append("")
        if abt.get("description_de"):
            lines.append(abt["description_de"])
            lines.append("")
        if (abt.get("blok_name") or "") == "Rezeption":
            lines.append(
                "**Schwerpunkt:** conditions paling lengkap "
                "(Check-in Andrang, Check-out, Telefon, Reservierungsänderung, "
                "Beschwerde, Night Audit, ruhige Schicht, Gruppenanreise)."
            )
            lines.append("")
        if abt.get("skip_blok"):
            lines.append("**Tidak diisi ke BLok.**")
            lines.append("")
        for item in abt.get("codes", []):
            aliases = item.get("aliases") or []
            alias_s = f" · alias: `{', '.join(aliases)}`" if aliases else ""
            lines.append(f"### `{item['code']}` — {item.get('name_de', '')}{alias_s}")
            lines.append("")
            lines.append("| Field | Nilai |")
            lines.append("|-------|-------|")
            lines.append(f"| Department | {item.get('department') or '-'} |")
            lines.append(f"| Lernfeld | {item.get('lernfeld') or '-'} |")
            lines.append(f"| Keywords | {', '.join(item.get('keywords') or []) or '-'} |")
            lines.append("")
            lines.append("**Default activities**")
            lines.append("")
            for d in item.get("default_activities_de") or []:
                lines.append(f"- {d}")
            lines.append("")
            lines.append("**Template teks Jerman (pool generator)**")
            lines.append("")
            for t in item.get("templates_de") or []:
                lines.append(f"- {t}")
            lines.append("")
            conds = item.get("conditions") or []
            lines.append(
                "**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`)."
            )
            lines.append("")
            if not conds:
                lines.append("- (belum ada condition)")
                lines.append("")
            for cond in conds:
                lines.append(f"- `{cond.get('id')}` — {cond.get('label_de', '')}")
                lines.append(f"  - when: `{format_when(cond.get('when'))}`")
                for t in cond.get("texts_de") or []:
                    lines.append(f"  - {t}")
            lines.append("")
    return "\n".join(lines)


def write_docs_markdown(katalog: dict[str, Any] | None = None) -> Path:
    text = format_catalog_markdown(katalog)
    DOCS_PATH.write_text(text, encoding="utf-8")
    return DOCS_PATH


def list_from_db(conn: sqlite3.Connection) -> str:
    """Tampilkan isi SQLite yang sedang ter-load (untuk pantau runtime)."""
    db.init_schema(conn)
    areas = list(conn.execute("SELECT * FROM work_areas ORDER BY code"))
    templates = list(
        conn.execute(
            "SELECT code, department, lernfeld, COUNT(*) AS n "
            "FROM activity_templates GROUP BY code, department, lernfeld "
            "ORDER BY department, code"
        )
    )
    lines = [
        "Database runtime (SQLite)",
        "=" * 40,
        f"Path: {db.DEFAULT_DB}",
        "",
        f"work_areas ({len(areas)}):",
    ]
    for a in areas:
        kw = json.loads(a["keywords_json"] or "[]")
        acts = json.loads(a["default_activities_json"] or "[]")
        lines.append(f"  • {a['code']} — {a['name_de']}")
        lines.append(f"    keywords: {', '.join(kw)}")
        lines.append(f"    default: {'; '.join(acts)}")
        raw_conditions = a["conditions_json"] if "conditions_json" in a.keys() else None
        conds = json.loads(raw_conditions or "[]")
        if conds:
            summary = ", ".join(
                f"{c.get('id')} ({format_when(c.get('when'))})" for c in conds
            )
            lines.append(f"    conditions: {summary}")
    lines.append("")
    lines.append(f"activity_templates (grouped, {len(templates)} codes):")
    for t in templates:
        lines.append(
            f"  • {t['code']} | {t['department'] or '-'} | "
            f"{t['lernfeld'] or '-'} | {t['n']} teks"
        )
    # detail teks
    lines.append("")
    lines.append("Detail teks per code:")
    for code_row in conn.execute(
        "SELECT DISTINCT code FROM activity_templates ORDER BY code"
    ):
        code = code_row["code"]
        lines.append(f"  [{code}]")
        for row in conn.execute(
            "SELECT text_de FROM activity_templates WHERE code = ? ORDER BY id",
            (code,),
        ):
            lines.append(f"    - {row['text_de']}")
    return "\n".join(lines).rstrip() + "\n"
