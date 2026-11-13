import argparse
import sys
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
    from content_studio.watch import WatchError, watch  # lazy: keeps other subcommands fast

    try:
        folder = watch(source, Path(out), transcribe)
    except WatchError as e:
        print(f"cs watch: {e}", file=sys.stderr)
        return 2
    print(folder.resolve())  # last line of stdout
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("hookscore", "detect"):
        return _passthrough(argv[0], argv[1:])
    p = argparse.ArgumentParser(prog="cs")
    p.add_argument("--version", action="store_true")
    sub = p.add_subparsers(dest="cmd", metavar="{hookscore,detect,beats,watch}")
    sub.add_parser("hookscore", help="score hooks (vendored; args pass through)")
    sub.add_parser("detect", help="flag AI-sounding text (vendored; args pass through)")
    sub.add_parser("beats", help="check a beats table: cs beats FILE").add_argument("file")
    w = sub.add_parser("watch", help="frame sheets and transcript of a reference video: cs watch SOURCE")
    w.add_argument("source", help="a local video file or a link")
    w.add_argument("--out", default="watch", help="output folder (default: ./watch)")
    w.add_argument("--no-transcript", action="store_true")
    args = p.parse_args(argv)
    if args.version:
        print(f"content-studio {VERSION}")
        return 0
    if args.cmd == "beats":
        return _beats(args.file)
    if args.cmd == "watch":
        return _watch(args.source, args.out, not args.no_transcript)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
