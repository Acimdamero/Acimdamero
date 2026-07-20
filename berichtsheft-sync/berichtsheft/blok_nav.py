"""Navigasi minggu kalender BLok (tab Woche + Jahresansicht fallback)."""

from __future__ import annotations

import re
from datetime import date, timedelta


def week_range(page) -> tuple[date | None, date | None]:
    body = page.inner_text("body")
    m = re.search(
        r"Kalenderwoche vom (\d{2})\.(\d{2})\.(\d{4}) bis (\d{2})\.(\d{2})\.(\d{4})",
        body,
    )
    if not m:
        return None, None
    d1, m1, y1, d2, m2, y2 = map(int, m.groups())
    return date(y1, m1, d1), date(y2, m2, d2)


def _click_week(page, direction: str) -> bool:
    sel = (
        'a[href*="weekBefore"]'
        if direction == "back"
        else 'a[href*="weekAfter"]'
    )
    loc = page.locator(sel)
    if not loc.count():
        back_text = page.locator(
            'a:has-text("Eine Woche zurück"), button:has-text("Eine Woche zurück")'
        )
        fwd_text = page.locator(
            'a:has-text("Eine Woche vor"), button:has-text("Eine Woche vor")'
        )
        loc = back_text if direction == "back" else fwd_text
    if not loc.count():
        return False
    loc.first.click(force=True)
    page.wait_for_load_state("networkidle", timeout=30000)
    page.wait_for_timeout(600)
    return True


def go_to_week_containing(page, target: date, *, max_steps: int = 55) -> bool:
    """Buka minggu yang memuat tanggal target (AJAX click, bukan goto URL)."""
    for _ in range(max_steps):
        ws, we = week_range(page)
        if ws and we and ws <= target <= we:
            return True
        if not ws or not we:
            return False
        if target < ws:
            if not _click_week(page, "back"):
                return False
        else:
            if not _click_week(page, "forward"):
                return False
    ws, we = week_range(page)
    return bool(ws and we and ws <= target <= we)


def _click_tab(page, label: str) -> bool:
    tab = page.locator(f'a:has-text("{label}")')
    if not tab.count():
        return False
    tab.first.click(force=True)
    page.wait_for_load_state("networkidle", timeout=30000)
    page.wait_for_timeout(500)
    return True


def go_to_week_via_jahresansicht(page, target: date) -> bool:
    """
    Fallback: tab Jahresansicht → klik minggu/KW yang memuat target → tab Woche.
    Tidak memakai page.goto(href) agar konten AJAX tetap valid.
    """
    if not _click_tab(page, "Jahresansicht"):
        return False

    monday = target - timedelta(days=target.weekday())
    kw = target.isocalendar()[1]
    candidates = [
        monday.strftime("%d.%m.%Y"),
        target.strftime("%d.%m.%Y"),
        f"{kw}. Kalenderwoche",
        f"KW {kw}",
        f"Kalenderwoche {kw}",
        str(kw),
    ]

    clicked = False
    for text in candidates:
        link = page.locator(f'a:has-text("{text}")')
        if link.count():
            link.first.click(force=True)
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(600)
            clicked = True
            break

    if not clicked:
        # Cari sel tabel yang memuat tanggal Senin minggu target
        mon_short = monday.strftime("%d.%m.")
        cell = page.locator(f'td:has-text("{mon_short}"), a:has-text("{mon_short}")')
        if cell.count():
            cell.first.click(force=True)
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(600)
            clicked = True

    if not clicked:
        return False

    _click_tab(page, "Woche")
    ws, we = week_range(page)
    return bool(ws and we and ws <= target <= we)


def go_to_week_containing_with_fallback(page, target: date, *, max_steps: int = 55) -> bool:
    """Coba weekBefore/weekAfter dulu; jika gagal, pakai Jahresansicht."""
    if go_to_week_containing(page, target, max_steps=max_steps):
        return True
    return go_to_week_via_jahresansicht(page, target)
