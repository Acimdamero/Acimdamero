"""Katalog kegiatan per Abteilung — load, tampil, sync ke SQLite & file sample."""

from __future__ import annotations

import json
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


def load_katalog(path: Path | None = None) -> dict[str, Any]:
    path = path or KATALOG_PATH
    return json.loads(path.read_text(encoding="utf-8"))


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
    """Load katalog into activity_templates + work_areas."""
    katalog = katalog or load_katalog()
    db.init_schema(conn)
    conn.execute("DELETE FROM activity_templates")
    conn.execute("DELETE FROM work_areas")

    templates = 0
    areas = 0
    for item in iter_codes(katalog):
        code = item["code"]
        department = item.get("department")
        lernfeld = item.get("lernfeld")
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
        )
        areas += 1
        for alias in item.get("aliases") or []:
            db.upsert_area(
                conn,
                alias,
                item.get("name_de", alias),
                item.get("keywords") or [],
                item.get("default_activities_de") or [],
            )
            areas += 1

    conn.commit()
    return {"templates": templates, "areas": areas}


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
    ]
    for abt in katalog.get("abteilungen", []):
        blok = abt.get("blok_name") or "(tanpa Abteilung / skip BLok)"
        lines.append(f"## {blok or 'Frei / skip'}")
        lines.append("")
        if abt.get("description_de"):
            lines.append(abt["description_de"])
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
