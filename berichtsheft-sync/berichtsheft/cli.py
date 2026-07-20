#!/usr/bin/env python3
"""CLI — init, import, orchestrate, worker, credentials, serve, bot."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from berichtsheft import catalog, credentials, db, generator, orchestrator
from berichtsheft.areas import load_areas_file
from berichtsheft.blok_worker import run_worker
from berichtsheft.seed import bootstrap, load_shifts

ROOT = Path(__file__).resolve().parent.parent


def cmd_init(_: argparse.Namespace) -> int:
    conn = db.connect()
    bootstrap(conn)
    n = load_areas_file(conn)
    conn.close()
    print(f"✓ {n} work areas geladen")
    print(f"\nDatenbank: {db.DEFAULT_DB}")
    print("Lanjut: docs/SETUP.md Fase 2 (credentials)")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_file():
        print(f"Datei nicht gefunden: {path}", file=sys.stderr)
        return 1
    conn = db.connect()
    db.init_schema(conn)
    n = load_shifts(conn, path)
    conn.close()
    print(f"✓ {n} Schichten importiert aus {path}")
    return 0


def cmd_areas_load(_: argparse.Namespace) -> int:
    conn = db.connect()
    db.init_schema(conn)
    n = load_areas_file(conn)
    conn.close()
    print(f"✓ {n} areas geladen")
    return 0


def cmd_catalog(args: argparse.Namespace) -> int:
    """Tampilkan / reload katalog kegiatan per Abteilung."""
    if args.reload:
        conn = db.connect()
        stats = catalog.sync_to_db(conn)
        catalog.export_legacy_files()
        conn.close()
        print(
            f"✓ Reload DB: {stats['templates']} templates, {stats['areas']} areas"
        )
        print(f"✓ Sync file: {catalog.AREAS_PATH.name}, {catalog.TEMPLATES_PATH.name}")

    if args.write_md:
        path = catalog.write_docs_markdown()
        print(f"✓ Docs: {path}")

    if args.db:
        conn = db.connect()
        print(catalog.list_from_db(conn), end="")
        conn.close()
        return 0

    if args.json:
        print(json.dumps(catalog.load_katalog(), ensure_ascii=False, indent=2))
        return 0

    if args.code:
        found = None
        for item in catalog.iter_codes():
            aliases = item.get("aliases") or []
            if item["code"] == args.code or args.code in aliases:
                found = item
                break
        if not found:
            print(f"Code tidak ditemukan: {args.code}", file=sys.stderr)
            return 1
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return 0

    if args.abteilung is not None:
        katalog = catalog.load_katalog()
        needle = args.abteilung.strip().lower()
        matched = [
            a
            for a in katalog.get("abteilungen", [])
            if (a.get("blok_name") or "").lower() == needle
            or needle in (a.get("description_de") or "").lower()
        ]
        if not matched:
            print(f"Abteilung tidak ditemukan: {args.abteilung}", file=sys.stderr)
            print("Pilihan:", ", ".join(
                (a.get("blok_name") or "Frei") for a in katalog.get("abteilungen", [])
            ))
            return 1
        print(catalog.format_catalog_text({"abteilungen": matched, "note": katalog.get("note", "")}), end="")
        return 0

    # default: tampilkan katalog file sumber
    if not args.reload and not args.write_md:
        print(catalog.format_catalog_text(), end="")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    conn = db.connect()
    if args.week:
        start, end = generator.parse_week(args.week)
    else:
        start, end = args.from_date, args.to_date
    drafts = generator.generate_range(conn, start, end)
    conn.close()
    print(f"✓ {len(drafts)} Entwürfe erzeugt ({start} … {end})")
    if args.json:
        print(json.dumps(drafts, ensure_ascii=False, indent=2))
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    conn = db.connect()
    if args.week:
        start, end = generator.parse_week(args.week)
    elif args.date:
        start = end = args.date
    else:
        start, end = args.from_date, args.to_date

    if args.date:
        shift = db.get_shift(conn, args.date)
        if not shift:
            print(f"Keine Schicht für {args.date}", file=sys.stderr)
            return 1
        draft = db.get_draft(conn, args.date)
        if not draft:
            draft_dict = generator.generate_for_date(conn, args.date)
            if draft_dict:
                print(generator.format_preview(draft_dict))
        else:
            print(generator.format_preview(dict(draft)))
        conn.close()
        return 0

    drafts = generator.generate_range(conn, start, end)
    for draft in drafts:
        print(generator.format_preview(draft))
        print()
    conn.close()
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    conn = db.connect()
    db.init_schema(conn)
    iso = args.date or orchestrator.today_iso()
    db.add_work_log(conn, iso, args.text, source="cli")
    conn.close()
    print(f"✓ Log gespeichert für {iso}")
    return 0


def cmd_finish(args: argparse.Namespace) -> int:
    conn = db.connect()
    db.init_schema(conn)
    iso = args.date or orchestrator.today_iso()
    try:
        draft = orchestrator.finish_day(conn, iso, args.summary)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    print(generator.format_preview(draft))
    if args.fill:
        result = run_worker(conn, iso, dry_run=not args.live, live=args.live)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    conn.close()
    return 0


def cmd_worker(args: argparse.Namespace) -> int:
    conn = db.connect()
    iso = args.date or orchestrator.today_iso()
    try:
        result = run_worker(conn, iso, dry_run=not args.live, live=args.live)
    except (ValueError, RuntimeError) as e:
        print(e, file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    conn.close()
    return 0


def cmd_credentials_set(args: argparse.Namespace) -> int:
    credentials.prompt_and_set(args.service)
    return 0


def cmd_credentials_test(args: argparse.Namespace) -> int:
    return 0 if credentials.test_credential(args.service) else 1


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    from berichtsheft.config_loader import load_config

    cfg = load_config()
    host = (cfg.get("server") or {}).get("host", "127.0.0.1")
    port = (cfg.get("server") or {}).get("port", 8765)
    if args.port:
        port = args.port
    print(f"API http://{host}:{port}")
    uvicorn.run("berichtsheft.api_server:app", host=host, port=port, reload=False)
    return 0


def cmd_bot(_: argparse.Namespace) -> int:
    from berichtsheft.telegram_bot import run_polling

    run_polling()
    return 0


def cmd_cursor_check(_: argparse.Namespace) -> int:
    from berichtsheft.config_loader import load_dotenv
    from berichtsheft.cursor_agent import is_available

    load_dotenv()
    if not is_available():
        print("✗ Cursor SDK belum siap")
        print("  1. Buat API key: cursor.com/dashboard → Integrations")
        print("  2. Isi CURSOR_API_KEY di .env")
        print("  3. npm install (di folder proyek)")
        return 1
    print("✓ CURSOR_API_KEY ada + scripts/cursor_prompt.mjs")
    if os.environ.get("CURSOR_API_KEY", "").strip():
        print("  (uji penuh: /ai di Telegram — butuh 1–5 menit)")
    return 0


def cmd_vision_check(_: argparse.Namespace) -> int:
    from berichtsheft.ai_vision import is_vision_enabled
    from berichtsheft.config_loader import load_dotenv

    load_dotenv()
    if not is_vision_enabled():
        print("✗ Vision tidak aktif")
        print("  GEMINI_API_KEY + AI_VISION_ENABLED=true di .env")
        return 1
    print("✓ Gemini Vision siap (kirim foto + caption di Telegram)")
    return 0


def cmd_gemini_check(_: argparse.Namespace) -> int:
    from berichtsheft.ai_gemini import is_enabled, polish_german

    if not is_enabled():
        print("✗ Gemini tidak aktif")
        print("  Isi GEMINI_API_KEY di .env — lihat docs/GEMINI.md")
        return 1
    try:
        sample, ok = polish_german(
            "Buffet aufgeräumt.", instruction="Ein formaler Satz für Berichtsheft."
        )
    except RuntimeError as e:
        print(f"⚠ {e}")
        return 1
    print("✓ Gemini aktif (key dikenali)")
    print(f"  Contoh: {sample[:200]}…" if len(sample) > 200 else f"  Contoh: {sample}")
    print(f"  API dipakai: {ok}")
    if not ok:
        print("  (Respons kosong — coba model lain di GEMINI_MODEL)")
    return 0 if ok else 1


def cmd_telegram_check(_: argparse.Namespace) -> int:
    from berichtsheft.telegram_setup import check_api_reachable, check_telegram_token

    api_ok = check_api_reachable()
    print(f"API lokal: {'✓' if api_ok else '✗'} (jalankan: python3 -m berichtsheft serve)")
    result = check_telegram_token()
    if result.get("ok"):
        print(f"✓ Bot @{result['username']} ({result['name']})")
        return 0 if api_ok else 1
    print(f"✗ {result.get('error')}")
    return 1


def cmd_telegram_init(_: argparse.Namespace) -> int:
    from berichtsheft.telegram_setup import ensure_env_file

    created = ensure_env_file()
    if created:
        print(f"✓ File dibuat: {ROOT / '.env'}")
        print("Edit .env → isi TELEGRAM_BOT_TOKEN dari @BotFather")
    else:
        print(".env sudah ada — edit TELEGRAM_BOT_TOKEN jika perlu")
    print("\nLangkah:")
    print("  1. Telegram → @BotFather → /newbot → salin token")
    print("  2. Buka .env di editor, paste token (tanpa kirim ke chat)")
    print("  3. python3 -m berichtsheft telegram-check")
    print("  4. Terminal A: python3 -m berichtsheft serve")
    print("  5. Terminal B: python3 -m berichtsheft bot")
    print("  6. HP: /start pada bot Anda")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    from berichtsheft.blok_audit import print_audit_summary, run_audit
    from berichtsheft.blok_gaps import analyze_week_gaps

    try:
        out = run_audit(args.from_date, args.to_date, headless=not args.headed)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1
    print(f"✓ Audit: {out}")
    report = json.loads(out.read_text(encoding="utf-8"))
    conn = db.connect()
    db.init_schema(conn)
    gap_weeks = [analyze_week_gaps(conn, w) for w in report.get("weeks") or []]
    conn.close()
    print_audit_summary(report, gap_weeks)
    return 0


def cmd_minggu(args: argparse.Namespace) -> int:
    from datetime import date

    from berichtsheft.blok_gaps import format_telegram_report, scan_weeks

    center = date.fromisoformat(args.date) if args.date else date.today()
    offsets = tuple(int(x) for x in args.offsets.split(","))
    conn = db.connect()
    db.init_schema(conn)
    try:
        scan = scan_weeks(conn, center, offsets=offsets, headless=not args.headed)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1
    finally:
        conn.close()
    print(format_telegram_report(scan))
    return 0


def cmd_test_flow(_: argparse.Namespace) -> int:
    """End-to-end simulation without Telegram/BLok live."""
    conn = db.connect()
    db.init_schema(conn)
    bootstrap(conn)
    iso = "2026-06-04"
    db.add_work_log(conn, iso, "Coffee break tagung ruang 3", source="test")
    db.add_work_log(conn, iso, "Bantu setup MEP pagi", source="test")
    draft = orchestrator.finish_day(conn, iso, "Selesai shift tagung")
    wr = run_worker(conn, iso, dry_run=True)
    conn.close()
    print("=== TEST FLOW OK ===")
    print(generator.format_preview(draft))
    print(json.dumps(wr, indent=2))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    conn = db.connect()
    if args.week:
        start, end = generator.parse_week(args.week)
    else:
        start, end = args.from_date, args.to_date
    rows = db.drafts_in_range(conn, start, end)
    out = [
        {
            "date": r["date"],
            "ort": r["ort"],
            "hours": r["hours"],
            "lernfeld": r["lernfeld"],
            "taetigkeiten": r["taetigkeiten"],
            "status": r["status"],
        }
        for r in rows
    ]
    conn.close()
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"✓ Export nach {args.output}")
    else:
        print(text)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Berichtsheft-Sync — Hotelfachmann")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="DB + seed").set_defaults(func=cmd_init)

    p_imp = sub.add_parser("import")
    p_imp.add_argument("file")
    p_imp.set_defaults(func=cmd_import)

    sub.add_parser("areas", help="load areas").set_defaults(func=cmd_areas_load)

    p_cat = sub.add_parser(
        "catalog",
        help="tampilkan/edit katalog kegiatan per Abteilung",
    )
    p_cat.add_argument(
        "--reload",
        action="store_true",
        help="muat ulang data/katalog_abteilung.json ke SQLite + sync file legacy",
    )
    p_cat.add_argument(
        "--write-md",
        action="store_true",
        help="tulis ulang docs/KATALOG_KEGIATAN.md dari JSON",
    )
    p_cat.add_argument(
        "--db",
        action="store_true",
        help="tampilkan isi SQLite runtime (bukan file JSON)",
    )
    p_cat.add_argument("--json", action="store_true", help="dump JSON mentah")
    p_cat.add_argument("--code", help="tampilkan satu code (mis. BRF, HK)")
    p_cat.add_argument(
        "--abteilung",
        help="filter Abteilung BLok (mis. Service, Housekeeping, Tagungen)",
    )
    p_cat.set_defaults(func=cmd_catalog)

    p_gen = sub.add_parser("generate")
    p_gen.add_argument("--week")
    p_gen.add_argument("--from", dest="from_date")
    p_gen.add_argument("--to", dest="to_date")
    p_gen.add_argument("--json", action="store_true")
    p_gen.set_defaults(func=cmd_generate)

    p_prev = sub.add_parser("preview")
    p_prev.add_argument("--week")
    p_prev.add_argument("--date")
    p_prev.add_argument("--from", dest="from_date")
    p_prev.add_argument("--to", dest="to_date")
    p_prev.set_defaults(func=cmd_preview)

    p_log = sub.add_parser("log", help="catatan saat kerja")
    p_log.add_argument("--date")
    p_log.add_argument("--text", required=True)
    p_log.set_defaults(func=cmd_log)

    p_fin = sub.add_parser("finish", help="orchestrate hari")
    p_fin.add_argument("--date")
    p_fin.add_argument("--summary", default="")
    p_fin.add_argument("--fill", action="store_true", help="jalankan worker")
    p_fin.add_argument("--live", action="store_true", help="BLok live (bukan dry-run)")
    p_fin.set_defaults(func=cmd_finish)

    p_w = sub.add_parser("worker")
    p_w.add_argument("--date")
    p_w.add_argument("--live", action="store_true", help="isi BLok sungguhan (butuh selector + Keychain)")
    p_w.set_defaults(func=cmd_worker)

    p_cs = sub.add_parser("credentials", help="Keychain")
    p_cs_sub = p_cs.add_subparsers(dest="cred_cmd", required=True)
    p_set = p_cs_sub.add_parser("set")
    p_set.add_argument("--service", default="blok")
    p_set.set_defaults(func=cmd_credentials_set)
    p_test = p_cs_sub.add_parser("test")
    p_test.add_argument("--service", default="blok")
    p_test.set_defaults(func=cmd_credentials_test)

    p_srv = sub.add_parser("serve", help="API server")
    p_srv.add_argument("--port", type=int)
    p_srv.set_defaults(func=cmd_serve)

    sub.add_parser("bot", help="Telegram polling").set_defaults(func=cmd_bot)
    sub.add_parser("telegram-init", help="buat .env + panduan BotFather").set_defaults(
        func=cmd_telegram_init
    )
    sub.add_parser("telegram-check", help="uji token + API").set_defaults(
        func=cmd_telegram_check
    )
    sub.add_parser("gemini-check", help="uji Gemini API key").set_defaults(
        func=cmd_gemini_check
    )
    sub.add_parser("vision-check", help="uji Gemini Vision").set_defaults(
        func=cmd_vision_check
    )
    sub.add_parser("cursor-check", help="uji Cursor SDK setup").set_defaults(
        func=cmd_cursor_check
    )
    sub.add_parser("test-flow", help="uji coba simulasi").set_defaults(func=cmd_test_flow)

    p_aud = sub.add_parser("audit", help="audit laporan BLok lama (Playwright)")
    p_aud.add_argument("--from", dest="from_date", required=True)
    p_aud.add_argument("--to", dest="to_date", required=True)
    p_aud.add_argument(
        "--headed",
        action="store_true",
        help="browser terlihat (default headless)",
    )
    p_aud.set_defaults(func=cmd_audit)

    p_mg = sub.add_parser("minggu", help="audit gap minggu lalu/ini/depan")
    p_mg.add_argument("--date", help="pusat scan YYYY-MM-DD (default hari ini)")
    p_mg.add_argument(
        "--offsets",
        default="-1,0,1",
        help="offset minggu dari pusat, mis. -1,0,1",
    )
    p_mg.add_argument("--headed", action="store_true")
    p_mg.set_defaults(func=cmd_minggu)

    p_exp = sub.add_parser("export")
    p_exp.add_argument("--week")
    p_exp.add_argument("--from", dest="from_date")
    p_exp.add_argument("--to", dest="to_date")
    p_exp.add_argument("-o", "--output")
    p_exp.set_defaults(func=cmd_export)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
