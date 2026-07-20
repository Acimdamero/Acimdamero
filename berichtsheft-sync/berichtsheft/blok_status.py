"""Deteksi status minggu BLok: bearbeitbar / freigegeben / abgenommen."""

from __future__ import annotations

import re
from typing import Any


def detect_week_status(page) -> dict[str, Any]:
    """
    Baca status minggu di halaman Woche.
    editable=True hanya jika textarea ada DAN minggu tidak terkunci abgenommen
    (kecuali Bearbeitungsmodus / editmodeCheck tersedia).
    """
    body = page.inner_text("body")
    body_lower = body.lower()

    has_textarea = page.locator('textarea[name$=":inputs:0:report"]').count() > 0
    editmode_check = page.locator(
        '#editmodeCheck, input[name="editmodeCheck"], input[id*="editmode"]'
    )
    bearbeitungsmodus = page.locator(
        'a:has-text("Bearbeitungsmodus"), button:has-text("Bearbeitungsmodus")'
    )
    has_editmode = editmode_check.count() > 0 or bearbeitungsmodus.count() > 0

    if re.search(r"\babgenommen\b", body_lower):
        status = "abgenommen"
    elif re.search(r"\bfreigegeben\b", body_lower):
        status = "freigegeben"
    elif has_textarea:
        status = "bearbeitbar"
    else:
        status = "unknown"

    locked = status == "abgenommen" and not has_editmode
    editable = has_textarea and not locked

    return {
        "status": status,
        "editable": editable,
        "locked": locked,
        "has_textarea": has_textarea,
        "has_editmode": has_editmode,
    }


def live_fill_allowed(page) -> tuple[bool, str]:
    """Apakah live_fill boleh jalan untuk minggu saat ini."""
    info = detect_week_status(page)
    if info["editable"]:
        return True, ""
    if info["status"] == "abgenommen":
        if info["has_editmode"]:
            return True, "Minggu abgenommen — mencoba Bearbeitungsmodus."
        return (
            False,
            "Minggu sudah abgenommen (ditandatangani Ausbilder). "
            "Edit manual di BLok atau aktifkan Bearbeitungsmodus.",
        )
    if not info["has_textarea"]:
        return False, "Minggu tidak memiliki field isian (textarea tidak ditemukan)."
    return False, f"Status minggu: {info['status']} — tidak bisa diisi otomatis."
