"""Analisis kekosongan Berichtsheft + laporan Telegram."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from berichtsheft import db
from berichtsheft.blok_audit import _audit_current_week, audit_range
from berichtsheft.blok_nav import go_to_week_containing
from berichtsheft.blok_worker import _blok_login
from berichtsheft.config_loader import load_config

FILL_TYPES = frozenset({"arbeit", "schule"})
WEEKDAY_DE = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _day_has_blok_content(day: dict[str, Any]) -> bool:
    text_len = day.get("text_len") or 0
    hours = (day.get("hours") or "").strip()
    if text_len > 0:
        return True
    if hours and hours not in ("0h:00min", "0h:00", "—", "-"):
        return True
    return False


def analyze_week_gaps(
    conn,
    week_audit: dict[str, Any],
) -> dict[str, Any]:
    """Bandingkan isi BLok dengan EdTime + data lokal."""
    ws_s = week_audit.get("week_start")
    we_s = week_audit.get("week_end")
    if not ws_s or not we_s:
        return {"issues": [], "summary": {}}

    ws = date.fromisoformat(ws_s)
    we = date.fromisoformat(we_s)
    shifts = {
        r["date"]: dict(r) for r in db.shifts_in_range(conn, ws_s, we_s)
    }

    issues: list[dict[str, Any]] = []
    missing_blok: list[str] = []
    missing_draft: list[str] = []
    pending_ok: list[str] = []
    unbound_photos: list[str] = []

    for day in week_audit.get("days") or []:
        iso = day.get("iso_date")
        if not iso:
            continue
        shift = shifts.get(iso)
        should_fill = bool(shift and shift["day_type"] in FILL_TYPES)
        has_content = _day_has_blok_content(day)

        if should_fill and not has_content:
            if week_audit.get("editable"):
                missing_blok.append(iso)
                issues.append(
                    {
                        "type": "blok_empty",
                        "date": iso,
                        "day": day.get("day"),
                        "day_type": shift["day_type"] if shift else None,
                        "severity": "high",
                        "message": f"{day.get('day')} {iso}: BLok kosong (EdTime: {shift['day_type']})",
                    }
                )
            else:
                issues.append(
                    {
                        "type": "blok_empty_locked",
                        "date": iso,
                        "severity": "info",
                        "message": f"{iso}: kosong tapi minggu tidak editable ({week_audit.get('status')})",
                    }
                )

        if should_fill:
            draft = db.get_draft(conn, iso)
            logs = db.work_logs_for_date(conn, iso)
            if logs and not draft:
                missing_draft.append(iso)
                issues.append(
                    {
                        "type": "no_draft",
                        "date": iso,
                        "severity": "medium",
                        "message": f"{iso}: ada log tapi belum /selesai",
                    }
                )
            elif draft and draft["status"] == "pending_review":
                approval = db.get_approval(conn, iso)
                if not approval or approval["status"] != "approved":
                    pending_ok.append(iso)
                    issues.append(
                        {
                            "type": "pending_ok",
                            "date": iso,
                            "severity": "medium",
                            "message": f"{iso}: draft siap — belum /ok",
                        }
                    )

        atts = db.attachments_for_date(conn, iso)
        for att in atts:
            if att["blok_status"] not in ("bound", "uploaded"):
                unbound_photos.append(f"#{att['id']} ({iso})")
                issues.append(
                    {
                        "type": "photo_not_uploaded",
                        "date": iso,
                        "attachment_id": att["id"],
                        "severity": "low",
                        "message": f"Foto #{att['id']} ({iso}) belum ke BLok — /lampirkan {att['id']}",
                    }
                )

    no_shift_days = []
    for i in range(7):
        iso = (ws + timedelta(days=i)).isoformat()
        if iso not in shifts:
            no_shift_days.append(iso)
            issues.append(
                {
                    "type": "no_edtime",
                    "date": iso,
                    "severity": "low",
                    "message": f"{iso}: tidak ada data EdTime — import jadwal?",
                }
            )

    return {
        "week_start": ws_s,
        "week_end": we_s,
        "status": week_audit.get("status"),
        "editable": week_audit.get("editable"),
        "issues": issues,
        "summary": {
            "missing_blok": missing_blok,
            "missing_draft": missing_draft,
            "pending_ok": pending_ok,
            "unbound_photos": unbound_photos,
            "no_edtime_days": no_shift_days,
            "issue_count": len(issues),
        },
    }


def scan_weeks(
    conn,
    center: date,
    offsets: tuple[int, ...] = (-1, 0, 1),
    *,
    headless: bool = True,
) -> dict[str, Any]:
    """Scan minggu lalu / ini / depan dalam satu sesi Playwright."""
    from berichtsheft import credentials

    cred = credentials.get_credential("blok")
    if not cred:
        raise RuntimeError("BLok credentials missing")

    cfg = load_config()
    blok = cfg.get("blok") or {}
    base_url = blok.get("base_url", "https://www.online-ausbildungsnachweis.de")
    selectors = blok.get("selectors") or {}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError("Install playwright") from e

    username, password = cred
    targets = [monday_of(center) + timedelta(weeks=o) for o in offsets]
    report: dict[str, Any] = {
        "center": center.isoformat(),
        "offsets": list(offsets),
        "weeks": [],
        "errors": [],
    }

    with sync_playwright() as p:
        page = p.chromium.launch(headless=headless).new_page()
        login_path = blok.get("login_path", "/blok/login")
        _blok_login(page, base_url, login_path, username, password, selectors)
        page.goto(base_url + "/blok/report", wait_until="networkidle", timeout=60000)

        for monday in targets:
            try:
                if not go_to_week_containing(page, monday + timedelta(days=3)):
                    report["errors"].append(f"Navigasi gagal KW {monday}")
                    continue
                week_data = _audit_current_week(page)
                gap = analyze_week_gaps(conn, week_data)
                report["weeks"].append({"audit": week_data, "gaps": gap})
            except Exception as e:
                report["errors"].append(f"KW {monday}: {e}")

        page.context.browser.close()

    report["summary"] = {
        "weeks_scanned": len(report["weeks"]),
        "total_issues": sum(
            w["gaps"]["summary"].get("issue_count", 0) for w in report["weeks"]
        ),
    }
    return report


def format_telegram_report(scan: dict[str, Any], *, compact: bool = False) -> str:
    lines = ["📊 Laporan Berichtsheft BLok", ""]

    if scan.get("errors"):
        lines.append("⚠ Peringatan:")
        for err in scan["errors"][:5]:
            lines.append(f"  • {err}")
        lines.append("")

    weeks = scan.get("weeks") or []
    if not weeks:
        lines.append("Tidak ada data minggu.")
        return "\n".join(lines)

    for item in weeks:
        audit = item["audit"]
        gaps = item["gaps"]
        s = gaps.get("summary") or {}
        ws, we = audit.get("week_start"), audit.get("week_end")
        status = audit.get("status", "?")
        editable = "✏️" if audit.get("editable") else "🔒"

        lines.append(f"{editable} KW {ws} – {we} ({status})")

        high = [i for i in gaps.get("issues", []) if i.get("severity") == "high"]
        medium = [i for i in gaps.get("issues", []) if i.get("severity") == "medium"]
        low = [i for i in gaps.get("issues", []) if i.get("severity") == "low"]

        if not high and not medium and not low:
            lines.append("  ✅ Minggu ini lengkap")
        else:
            for issue in (high + medium)[:8 if compact else 20]:
                icon = "🔴" if issue["severity"] == "high" else "🟡"
                lines.append(f"  {icon} {issue['message']}")
            if low and not compact:
                for issue in low[:5]:
                    lines.append(f"  🔵 {issue['message']}")

        filled = audit.get("days_filled", 0)
        lines.append(f"  📈 Hari terisi di BLok: {filled}/7")
        lines.append("")

    total = scan.get("summary", {}).get("total_issues", 0)
    if total:
        lines.append(f"Total isu: {total}")
        lines.append("/selesai → draft · /ok → isi BLok · /lampirkan ID → foto")
    else:
        lines.append("✅ Semua minggu terpantau OK")

    return "\n".join(lines)[:4000]


def quick_gap_check(conn, *, headless: bool = True) -> str:
    """Pesan singkat untuk reminder otomatis."""
    today = date.today()
    scan = scan_weeks(conn, today, offsets=(-1, 0, 1), headless=headless)
    return format_telegram_report(scan, compact=True)
