"""DirTidy — keep your Downloads folder tidy, automatically.

Watch a folder, sort new files into category subfolders by extension,
and undo any batch with a single command. Pure standard library.
"""

from .mover import MovePlan, plan_moves, run_once, undo_moves
from .rules import DEFAULT_RULES, category_for, load_rules

__version__ = "1.0.0"

__all__ = [
    "DEFAULT_RULES",
    "MovePlan",
    "category_for",
    "load_rules",
    "plan_moves",
    "run_once",
    "undo_moves",
    "__version__",
]
