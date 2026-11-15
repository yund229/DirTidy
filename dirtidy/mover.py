"""Planning, executing and undoing file moves.

Every executed batch is appended to a JSONL journal (``.dirtidy.jsonl``)
inside the watched folder, one line per move::

    {"time": "...", "src": "...", "dst": "...", "category": "..."}

``undo_moves`` replays the journal in reverse and restores files.
"""

from __future__ import annotations

import json
import shutil
import uuid
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .rules import category_for

JOURNAL_NAME = ".dirtidy.jsonl"


@dataclass(frozen=True)
class MovePlan:
    """A single planned move from the watched folder into a category."""

    src: Path
    dst: Path
    category: str


def journal_path(folder: Path) -> Path:
    return folder / JOURNAL_NAME


def unique_destination(dst: Path) -> Path:
    """Return *dst*, or ``name (1).ext`` / ``name (2).ext`` ... if taken."""
    if not dst.exists():
        return dst
    stem, suffix = dst.stem, dst.suffix
    for i in range(1, 1000):
        candidate = dst.with_name(f"{stem} ({i}){suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"no free name for {dst}")


def plan_moves(
    folder: Path, rules: dict[str, tuple[str, ...]]
) -> list[MovePlan]:
    """Plan moves for top-level files in *folder*.

    Skipped: subdirectories, dotfiles, the journal file itself and any
    file whose extension matches no rule.  Unmatched files stay put.
    """
    folder = Path(folder)
    reserved = {folder / category for category in rules}
    reserved.add(journal_path(folder))
    plans: list[MovePlan] = []
    for entry in sorted(folder.iterdir()):
        if not entry.is_file():
            continue
        if entry.name.startswith("."):
            continue
        if entry in reserved:
            continue
        category = category_for(entry.name, rules)
        if category is None:
            continue
        dst_dir = folder / category
        dst = unique_destination(dst_dir / entry.name)
        plans.append(MovePlan(src=entry, dst=dst, category=category))
    return plans


def execute_moves(plans: list[MovePlan], *, dry_run: bool = False) -> list[dict]:
    """Execute *plans*, journaling the batch (unless *dry_run*).

    Returns the journal entries for the moves that were performed.
    A dry run moves nothing and returns ``[]``.
    """
    if dry_run or not plans:
        return []
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    batch_id = uuid.uuid4().hex
    entries: list[dict] = []
    for plan in plans:
        plan.dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(plan.src), str(plan.dst))
        entries.append(
            {
                "time": timestamp,
                "batch": batch_id,
                "src": str(plan.src),
                "dst": str(plan.dst),
                "category": plan.category,
            }
        )
    _append_journal(plans[0].src.parent, entries)
    return entries


def run_once(
    folder: Path, rules: dict[str, tuple[str, ...]], *, dry_run: bool = False
) -> list[dict]:
    """Plan and (unless dry run) execute one tidying pass over *folder*."""
    plans = plan_moves(folder, rules)
    return execute_moves(plans, dry_run=dry_run)


def _append_journal(folder: Path, entries: list[dict]) -> None:
    with journal_path(folder).open("a", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_journal(folder: Path) -> list[dict]:
    """Parse the journal, silently skipping malformed lines."""
    path = journal_path(folder)
    if not path.exists():
        return []
    entries: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict) and "src" in entry and "dst" in entry:
            entries.append(entry)
    return entries


def _remove_empty_dirs(folder: Path, dirs: set[Path]) -> None:
    """Delete category dirs left empty by an undo (never the folder itself)."""
    for d in dirs:
        if d == folder:
            continue
        with suppress(OSError):
            d.rmdir()  # only succeeds when empty


def undo_moves(folder: Path, *, all: bool = False) -> list[dict]:
    """Undo the most recent batch (or all batches) and rewrite the journal.

    Files whose destination no longer exists are skipped.  A file whose
    original spot is taken again is restored under a `` (n)`` name.
    """
    entries = read_journal(folder)
    if not entries:
        return []
    if all:
        batch = list(entries)
    else:
        last = entries[-1]
        # group by explicit batch id; fall back to timestamp for older journals
        field = "batch" if "batch" in last else "time"
        key = last[field]
        batch = [e for e in entries if e.get(field) == key]
    batch_ids = {id(e) for e in batch}

    restored: list[dict] = []
    for entry in reversed(batch):
        dst = Path(entry["dst"])
        src = Path(entry["src"])
        if not dst.exists():
            continue
        src.parent.mkdir(parents=True, exist_ok=True)
        target = src if not src.exists() else unique_destination(src)
        shutil.move(str(dst), str(target))
        restored.append({**entry, "restored_to": str(target)})

    _remove_empty_dirs(folder, {Path(e["dst"]).parent for e in batch})

    remaining = [e for e in entries if id(e) not in batch_ids]
    journal = journal_path(folder)
    if remaining:
        with journal.open("w", encoding="utf-8") as fh:
            for entry in remaining:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    elif journal.exists():
        journal.unlink()
    return restored
