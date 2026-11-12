import argparse

VERSION = "0.1.0"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cs")
    p.add_argument("--version", action="store_true")
    p.add_subparsers(dest="cmd")  # later tasks register subcommands here
    args = p.parse_args(argv)
    if args.version:
        print(f"content-studio {VERSION}")
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
