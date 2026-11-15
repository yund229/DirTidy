# DirTidy 🧹

**English** | [中文](README.md)

Keep your Downloads folder clean automatically. DirTidy watches a folder, sorts files into category subfolders by extension, and lets you undo everything with one command.

[![CI](https://github.com/yund229/DirTidy/actions/workflows/ci.yml/badge.svg)](https://github.com/yund229/DirTidy/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

![demo](https://cdn.jsdelivr.net/gh/yund229/DirTidy@main/assets/demo.gif)

## Features

- **Zero dependencies** — pure Python standard library, no watchdog, no yaml
- **Auto sorting** — 9 categories out of the box: Images / Documents / Archives / Installers / Videos / Audio / Fonts / Code / Torrents
- **Custom rules** — dump the defaults with `--dump-rules`, edit, load with `--rules`
- **Dry run** — `--dry-run` shows what would happen before touching anything
- **One-command undo** — every pass is journaled to JSONL; `--undo` reverts the last batch, `--undo-all` reverts everything
- **No overwrites** — name conflicts are resolved as `file (1).jpg`
- **Cross-platform** — identical behavior on Windows / macOS / Linux, plus a portable Windows exe
- **65 unit tests** — CI matrix across Python 3.9 / 3.11 / 3.13 × Ubuntu / Windows

## Installation

```bash
pip install git+https://github.com/yund229/DirTidy.git
```

Or grab the portable `DirTidy.exe` from the [Releases](https://github.com/yund229/DirTidy/releases) page (Windows, no Python needed).

## Quick start

```bash
# tidy once
dirtidy ~/Downloads

# preview what would be moved, without moving anything
dirtidy ~/Downloads --dry-run

# keep watching: sort new files as they appear (Ctrl+C to stop)
dirtidy ~/Downloads --watch

# undo the last batch / undo everything
dirtidy ~/Downloads --undo
dirtidy ~/Downloads --undo-all
```

Without installing, run it as a module:

```bash
python -m dirtidy ~/Downloads --watch --dry-run
```

## Custom rules

```bash
dirtidy --dump-rules myrules.json    # export the default rules
# edit myrules.json, e.g. add "Study": [".pptx", ".epub"]
dirtidy ~/Downloads --rules myrules.json
```

A `--rules` file **replaces** the defaults entirely (it is not merged), so start from `--dump-rules`. Files matching no rule stay in place; dotfiles and the `.dirtidy.jsonl` journal are always skipped.

## How it works

1. **Scan** — top-level files of the target folder (no recursion)
2. **Classify** — extension → category via the rule table
3. **Conflict** — if the destination exists, rename to `name (1).ext`
4. **Move** — perform the move and append `src → dst` to a JSONL journal
5. **Undo** — replay the journal in reverse; if the original spot is taken, restore under a numbered name

The watcher polls the directory (default every 3 s) instead of using platform-specific filesystem event APIs, so behavior is identical on all three OSes and easy to test.

## License

[MIT](LICENSE)
