"""Polling watcher: run a tidying pass whenever the folder changes.

DirTidy uses simple directory polling instead of filesystem event APIs,
which keeps it dependency-free and identical in behaviour across
Windows, macOS and Linux.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from .mover import run_once

#: Called with the journal entries of a finished pass (possibly empty).
BatchCallback = Callable[[list[dict]], None]


def snapshot(folder: Path) -> dict[str, float]:
    """Return ``{name: mtime}`` for files and ``{name/: 0.0}`` for dirs."""
    snap: dict[str, float] = {}
    for entry in folder.iterdir():
        try:
            if entry.is_file():
                snap[entry.name] = entry.stat().st_mtime
            elif entry.is_dir():
                snap[entry.name + "/"] = 0.0
        except OSError:  # file vanished mid-scan
            continue
    return snap


def watch(
    folder: Path,
    rules: dict[str, tuple[str, ...]],
    *,
    interval: float = 3.0,
    dry_run: bool = False,
    should_stop: Callable[[], bool] | None = None,
    on_batch: BatchCallback | None = None,
) -> None:
    """Tidy once immediately, then again after every observed change.

    ``should_stop`` is polled each cycle so callers can integrate their
    own shutdown signal (e.g. ``event.is_set`` from a thread or signal
    handler).  Ctrl+C also stops the loop naturally.
    """
    folder = Path(folder)

    def pass_and_notify() -> None:
        entries = run_once(folder, rules, dry_run=dry_run)
        if on_batch is not None:
            on_batch(entries)

    pass_and_notify()
    last = snapshot(folder)
    while should_stop is None or not should_stop():
        time.sleep(interval)
        current = snapshot(folder)
        if current == last:
            continue
        pass_and_notify()
        # re-snapshot after the pass so the moves it performed are not
        # mistaken for another change on the next cycle
        last = snapshot(folder)
