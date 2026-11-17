import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from content_studio.beats import check_beats, parse_beats

VERSION = "0.1.0"


def _passthrough(name: str, argv: list[str]) -> int:
    """Run a vendored scorer's own main() with its own arguments."""
    if name == "hookscore":
        from content_studio.vendor.hookscore import main as vendored
    else:
        from content_studio.vendor.detect import main as vendored
    saved, sys.argv = sys.argv, [f"cs {name}", *argv]
    try:
        vendored()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    finally:
        sys.argv = saved
    return 0


def _beats(path: str) -> int:
    try:
        with open(path, encoding="utf-8-sig") as f:
            flags = check_beats(parse_beats(f.read()))
    except (OSError, ValueError) as e:
        print(f"cs beats: {e}", file=sys.stderr)
        return 2
    for flag in flags:
        print(flag)
    return 1 if flags else 0


def _watch(source: str, out: str, transcribe: bool) -> int:
    from content_studio.watch import watch  # lazy: keeps other subcommands fast

    try:
        folder = watch(source, Path(out), transcribe)
    except ValueError as e:  # WatchError, or the shared ffmpeg/probe helpers
        print(f"cs watch: {e}", file=sys.stderr)
        return 2
    print(folder.resolve())  # last line of stdout
    return 0


def _read_json(path: str):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def _doctor(as_json: bool, allow: bool, url: str | None) -> int:
    from content_studio import doctor

    if allow:
        print(json.dumps(doctor.allow_list(), indent=2))
        return 0
    if url:
        ok, msg = doctor.probe_url(url)
        print(msg)
        return 0 if ok else 1
    checks = doctor.run_checks()
    ok = all(c.ok for c in checks if c.required)
    doctor.write_marker(ok)
    print(json.dumps([asdict(c) for c in checks], indent=2) if as_json else doctor.report(checks))
    if not ok:
        print("\nSome required tools are MISSING. Run the fix lines above, then run the doctor again.", file=sys.stderr)
    return 0 if ok else 1


def _packet(options: str, evidence: str, out: str, seed: int) -> int:
    from content_studio.packet import build_packet

    try:
        opts = _read_json(options)
        if not isinstance(opts, list) or not opts or not all(isinstance(o, dict) for o in opts):
            raise ValueError("options.json must be a non-empty list of options")
        text, labels = build_packet(opts, Path(evidence).read_text(encoding="utf-8-sig"), seed)
        o = Path(out)
        o.write_text(text, encoding="utf-8")
        o.with_name("packet.map.json").write_text(json.dumps(labels, indent=2), encoding="utf-8")
    except (OSError, ValueError, KeyError) as e:  # json.JSONDecodeError is a ValueError
        print(f"cs packet: {e!r}" if isinstance(e, KeyError) else f"cs packet: {e}", file=sys.stderr)
        return 2
    print(o.resolve())
    return 0


def _verify(packet: str, marks: str, out_there: str) -> int:
    from content_studio.verify import verify_marks

    try:
        marked = _read_json(marks)
        if not isinstance(marked, list):
            raise ValueError("marks must be a JSON list")
        results = verify_marks(Path(packet).read_text(encoding="utf-8-sig"), marked, {x.strip() for x in out_there.split(",") if x.strip()})
    except (OSError, ValueError) as e:
        print(f"cs verify: {e}", file=sys.stderr)
        return 2
    print(json.dumps(results, indent=2))
    return 0 if any(not r["dropped"] for r in results) else 3


def _brandcheck(path: str, filled: bool) -> int:
    from content_studio.brand import check_brand

    problems = check_brand(Path(path), filled)
    for line in problems:
        print(line)
    return 1 if problems else 0


def _workspace(path: str) -> int:
    from content_studio.brand import check_workspace

    msg = check_workspace(Path(path), Path.home())
    if msg:
        print(f"cs workspace: {msg}", file=sys.stderr)
    return 1 if msg else 0


def _check(file: str, as_json: bool) -> int:
    from content_studio.check import check_video

    try:
        r = check_video(Path(file))
    except ValueError as e:
        print(f"cs check: {e}", file=sys.stderr)
        return 2
    if as_json:
        print(json.dumps(r, indent=2))
    else:
        i = r["info"]
        print(f"{i['width']}x{i['height']}, {i['fps']} fps, {i['duration']:.1f} s, audio: {'yes' if i['audio'] else 'NO'}, loudness: {i['lufs']} LUFS")
        for flag in r["flags"]:
            print(f"FLAG {flag}")
    return 1 if r["flags"] else 0


def _cover(video: str, at: float, title: str, out: str | None, sheet: bool) -> int:
    from content_studio.cover import make_cover, make_sheet

    v = Path(video)
    try:
        made = make_sheet(v, Path(out or v.with_suffix(".sheet.jpg"))) if sheet else make_cover(v, Path(out or v.with_suffix(".cover.jpg")), at, title)
    except ValueError as e:
        print(f"cs cover: {e}", file=sys.stderr)
        return 2
    print(Path(made).resolve())
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("hookscore", "detect"):
        return _passthrough(argv[0], argv[1:])
    p = argparse.ArgumentParser(prog="cs")
    p.add_argument("--version", action="store_true")
    sub = p.add_subparsers(dest="cmd", metavar="{doctor,workspace,brandcheck,packet,verify,beats,check,cover,watch,hookscore,detect}")
    sub.add_parser("hookscore", help="score hooks (vendored; args pass through)")
    sub.add_parser("detect", help="flag AI-sounding text (vendored; args pass through)")
    sub.add_parser("beats", help="check a beats table: cs beats FILE").add_argument("file")
    w = sub.add_parser("watch", help="frame sheets and transcript of a reference video: cs watch SOURCE")
    w.add_argument("source", help="a local video file or a link")
    w.add_argument("--out", default="watch", help="output folder (default: ./watch)")
    w.add_argument("--no-transcript", action="store_true")
    d = sub.add_parser("doctor", help="check what is missing and how to fix it")
    d.add_argument("--json", action="store_true")
    d.add_argument("--allow", action="store_true", help="print the permission rules to paste into .claude/settings.json")
    d.add_argument("--url", help="test whether a link can be downloaded")
    sub.add_parser("workspace", help="refuse your home folder as a project folder: cs workspace PATH").add_argument("path")
    b = sub.add_parser("brandcheck", help="check brands/<brand>/ has all five files and headings")
    b.add_argument("dir")
    b.add_argument("--filled", action="store_true", help="template prompts do not count as answers")
    k = sub.add_parser("packet", help="build the blind critic packet from options.json and evidence")
    k.add_argument("--options", required=True)
    k.add_argument("--evidence", required=True)
    k.add_argument("--out", required=True)
    k.add_argument("--seed", type=int, default=0)
    v = sub.add_parser("verify", help="check the critic's marks against the packet")
    v.add_argument("--packet", required=True)
    v.add_argument("--marks", required=True)
    v.add_argument("--out-there", default="", help="labels (A,C) that are never dropped on score alone")
    c = sub.add_parser("check", help="check a finished video: 9:16, 30 fps, audio, loudness")
    c.add_argument("file")
    c.add_argument("--json", action="store_true")
    cv = sub.add_parser("cover", help="make a cover frame (and grid preview) or a contact sheet")
    cv.add_argument("video")
    cv.add_argument("--at", type=float, default=1.0)
    cv.add_argument("--title", default="")
    cv.add_argument("--out")
    cv.add_argument("--sheet", action="store_true")
    args = p.parse_args(argv)
    if args.version:
        print(f"content-studio {VERSION}")
        return 0
    handlers = {
        "doctor": lambda: _doctor(args.json, args.allow, args.url),
        "workspace": lambda: _workspace(args.path),
        "brandcheck": lambda: _brandcheck(args.dir, args.filled),
        "packet": lambda: _packet(args.options, args.evidence, args.out, args.seed),
        "verify": lambda: _verify(args.packet, args.marks, args.out_there),
        "check": lambda: _check(args.file, args.json),
        "cover": lambda: _cover(args.video, args.at, args.title, args.out, args.sheet),
        "beats": lambda: _beats(args.file),
        "watch": lambda: _watch(args.source, args.out, not args.no_transcript),
    }
    if args.cmd in handlers:
        return handlers[args.cmd]()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
