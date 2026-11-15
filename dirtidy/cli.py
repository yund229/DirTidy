"""Command line interface.

::

    python -m dirtidy <folder> [--watch] [--dry-run] [--undo] [--undo-all]
                       [--rules FILE] [--interval SEC] [--dump-rules FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .mover import undo_moves
from .rules import DEFAULT_RULES, load_rules
from .watcher import watch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dirtidy",
        description="Automatically sort a folder's files into category subfolders.",
    )
    parser.add_argument("folder", nargs="?", help="folder to tidy (e.g. ~/Downloads)")
    parser.add_argument(
        "--watch", action="store_true", help="keep watching and tidy on every change"
    )
    parser.add_argument(
        "--interval", type=float, default=3.0, metavar="SEC",
        help="polling interval for --watch (default: 3)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print planned moves without moving"
    )
    parser.add_argument("--undo", action="store_true", help="undo the last batch")
    parser.add_argument("--undo-all", action="store_true", help="undo every batch")
    parser.add_argument("--rules", metavar="FILE", help="JSON rules file (replaces defaults)")
    parser.add_argument(
        "--dump-rules", metavar="FILE",
        help="write the default rules to FILE as a starting point, then exit",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _describe(entry: dict) -> str:
    src = Path(entry["src"])
    dst = Path(entry["dst"])
    return f"{src.name} -> {dst.parent.name}/{dst.name}"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.dump_rules:
        out = Path(args.dump_rules)
        out.write_text(
            json.dumps(
                {k: list(v) for k, v in DEFAULT_RULES.items()},
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"default rules written to {out}")
        return 0

    if not args.folder:
        build_parser().error("a folder is required (or use --dump-rules)")

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"error: not a folder: {folder}", file=sys.stderr)
        return 2

    try:
        rules = load_rules(args.rules)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: cannot load rules: {exc}", file=sys.stderr)
        return 2

    if args.undo or args.undo_all:
        restored = undo_moves(folder, all=args.undo_all)
        if restored:
            print(f"restored {len(restored)} file(s):")
            for entry in restored:
                print(f"  {_describe(entry)}")
        else:
            print("nothing to undo")
        return 0

    if args.watch:
        print(f"watching {folder} every {args.interval:g}s (Ctrl+C to stop)")
        if args.dry_run:
            print("dry run: nothing will actually be moved")
        try:
            watch(
                folder, rules, interval=args.interval, dry_run=args.dry_run,
                on_batch=lambda entries: [
                    print(f"moved: {_describe(e)}") for e in entries
                ],
            )
        except KeyboardInterrupt:
            print("\nstopped")
        return 0

    from .mover import execute_moves, plan_moves

    plans = plan_moves(folder, rules)
    if args.dry_run:
        if not plans:
            print("no moves planned")
            return 0
        print(f"{len(plans)} move(s) planned:")
        for plan in plans:
            print(f"  {plan.src.name} -> {plan.category}/{plan.dst.name}")
        return 0
    entries = execute_moves(plans)
    if not entries:
        print("nothing to tidy")
        return 0
    print(f"{len(entries)} file(s) moved:")
    for entry in entries:
        print(f"  {_describe(entry)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
