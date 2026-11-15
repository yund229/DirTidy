"""File classification rules.

Rules are an ordered mapping of ``category -> tuple of extensions``.
The first category whose extension list contains a file's (lowercased)
suffix wins, so order matters when an extension appears twice.
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_RULES: dict[str, tuple[str, ...]] = {
    "Images": (
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg",
        ".ico", ".tif", ".tiff", ".heic", ".avif",
    ),
    "Documents": (
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".txt", ".md", ".rtf", ".odt", ".csv", ".epub",
    ),
    "Archives": (
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".zst", ".iso",
    ),
    "Installers": (
        ".exe", ".msi", ".msix", ".dmg", ".apk", ".appimage",
    ),
    "Videos": (
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
    ),
    "Audio": (
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus",
    ),
    "Fonts": (".ttf", ".otf", ".woff", ".woff2"),
    "Code": (
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".java",
        ".c", ".cpp", ".h", ".go", ".rs", ".php", ".rb", ".swift", ".kt",
        ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".sh", ".bat",
        ".ps1", ".sql",
    ),
    "Torrents": (".torrent",),
}


def _normalize(rules: dict) -> dict[str, tuple[str, ...]]:
    return {
        category: tuple(ext.lower() for ext in exts)
        for category, exts in rules.items()
    }


def load_rules(path: str | Path | None = None) -> dict[str, tuple[str, ...]]:
    """Return the default rules, or rules loaded from a JSON file.

    The JSON file fully defines the classification (it does not merge
    with the defaults).  Use ``python -m dirtidy --dump-rules`` to write
    a copy of the defaults that you can edit.
    """
    if path is None:
        return {k: tuple(v) for k, v in DEFAULT_RULES.items()}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(
        isinstance(v, list) for v in data.values()
    ):
        raise ValueError(
            "rules file must be a JSON object mapping category -> list of extensions"
        )
    return _normalize(data)


def category_for(filename: str, rules: dict[str, tuple[str, ...]]) -> str | None:
    """Return the category for *filename*, or ``None`` if unmatched."""
    suffix = Path(filename).suffix.lower()
    if not suffix:
        return None
    for category, exts in rules.items():
        if suffix in exts:
            return category
    return None
