"""Indonesian / English work notes → formal German (Berichtsheft style)."""

from __future__ import annotations

import re

# Longest phrases first (order matters)
PHRASES: list[tuple[str, str]] = [
    (r"coffee\s*break", "Coffee-Break"),
    (r"check\s*(-?\s*)?in", "Check-in"),
    (r"check\s*(-?\s*)?out", "Check-out"),
    (r"frühstück|fruhstuck|breakfast", "Frühstück"),
    (r"housekeeping", "Housekeeping"),
    (r"tagung|konferenz|meeting", "Tagung"),
    (r"schloss", "Schloss"),
    (r"besteck", "Besteck"),
    (r"buffet", "Buffet"),
    (r"station\s*kopi", "Kaffeestation"),
    (r"membereskan\s+buffet", "Buffet abgebaut"),
    (r"membersihkan\s+meja", "Tische abgeräumt und gereinigt"),
    (r"mencuci\s+piring", "Geschirr gespült"),
    (r"mengangkat\s+piring|mengampil\s+piring", "schmutziges Geschirr eingesammelt"),
    (r"menawarkan\s+kopi", "Gästen Kaffee angeboten"),
    (r"persiapan\s+station", "Station vorbereitet"),
    (r"datang\s+shift\s+pagi", "Frühschicht angetreten"),
    (r"pindah\s+ke\s+tagung", "zur Tagungsbetreuung gewechselt"),
    (r"shift\s+tagung\s+beendet", "Schicht in der Tagung beendet"),
    (r"shift\s+beendet", "Schicht beendet"),
    (r"schicht\s+tagung\s+beendet", "Schicht in der Tagung beendet"),
    (r"selesai", "Schicht beendet"),
    (r"setup\s+mep", "MEP-Vorbereitung"),
    (r"\bbantu\b", "unterstützt bei"),
    (r"\bpagi\b", "morgens"),
    (r"\bruang\s*(\d+)", r"Raum \1"),
    (r"\blantai\s*(\d+)", r"Etage \1"),
    (r"\btamu\b", "Gäste"),
    (r"\bkebutuhan\b", "Bedürfnisse"),
    (r"\balergi\b", "Allergien"),
    (r"\bkedatangan\b", "Ankunft"),
    (r"\bceklist\b|cek\s+list", "Checkliste"),
    (r"\bmemperhatikan\b", "beobachtet"),
    (r"\bmengganti\b", "ausgetauscht"),
    (r"\btisu\b", "Servietten"),
    (r"\bmangkuk\b", "Schüsseln"),
    (r"\bgelas\b", "Gläser"),
    (r"\bpiring\b", "Geschirr"),
    (r"\bkotor\b", "Abwäsche"),
    (r"\bbersihkan\b", "gereinigt"),
    (r"\bmenyiapkan\b", "vorbereitet"),
]

# Whole-line templates for very common Azubi notes
LINE_TEMPLATES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"datang.*fr[uü]hst[uü]ck.*7", re.I),
        "Frühschicht im Frühstück um 07:00 Uhr angetreten und die Station vorbereitet.",
    ),
    (
        re.compile(r"checklist.*tamu|ceklist.*tamu", re.I),
        "Checkliste für Gästeanreise erstellt und besondere Bedürfnisse (z. B. Allergien) notiert.",
    ),
    (
        re.compile(r"membereskan.*buffet|buffet.*piring", re.I),
        "Buffet abgebaut, Geschirr und Besteck zur Spülküche gebracht und mitgeholfen.",
    ),
    (
        re.compile(r"pindah.*tagung.*schloss", re.I),
        "Im Anschluss zur Tagungsbetreuung im Schloss gewechselt.",
    ),
]


def translate_note_to_de(note: str) -> str:
    text = " ".join(note.strip().split())
    if not text:
        return ""

    for pattern, replacement in LINE_TEMPLATES:
        if pattern.search(text):
            return replacement

    out = text
    for pat, rep in PHRASES:
        out = re.sub(pat, rep, out, flags=re.IGNORECASE)

    # Remove leftover ID filler words
    fillers = [
        r"\bdi\b", r"\bke\b", r"\bdan\b", r"\byang\b", r"\buntuk\b",
        r"\bdengan\b", r"\bapakah\b", r"\bsemuanya\b", r"\blalu\b",
        r"\bmac\b", r"\bmenyala\b", r"\bcek\b",
    ]
    for f in fillers:
        out = re.sub(f, " ", out, flags=re.IGNORECASE)

    out = re.sub(r"\s+", " ", out).strip()
    out = re.sub(r"-Break-Break", "-Break", out, flags=re.IGNORECASE)

    # If still mostly non-German (heuristic: many short latin words), wrap as activity sentence
    if _needs_sentence_wrap(out):
        out = _wrap_as_activity(out)

    if out and out[0].islower():
        out = out[0].upper() + out[1:]
    if out and not out.endswith("."):
        out += "."
    return out


def _needs_sentence_wrap(text: str) -> bool:
    id_markers = ("ruang", "pagi", "bantu", "meng", "mem", "men", "dan ", "yang ")
    lower = text.lower()
    return any(m in lower for m in id_markers) or len(text.split()) > 12


def _wrap_as_activity(fragment: str) -> str:
    fragment = fragment.strip(" ,.;")
    if not fragment:
        return "Tätigkeiten im Betrieb durchgeführt."
    starters = ("unterstützt", "Frühstück", "Tagung", "Coffee", "Buffet", "Gäste")
    if not any(fragment.startswith(s) for s in starters):
        return f"Tätigkeit: {fragment}."
    return f"{fragment}."


def dedupe_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        key = line.strip().lower()
        if key not in seen:
            seen.add(key)
            out.append(line)
    return out
