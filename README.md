# File Organizer

A configurable CLI for scanning files from multiple sources and organizing them into a destination structure.

> **Safety default:** `organize` runs in dry-run mode unless you pass `--execute`.

## Current repository state

This repository currently contains two project trees:

- The **active Python package code** is under `file-organizer/file_organizer/`.
- There is also a duplicated top-level layout (`README.md`, `tests/`, `setup.py`, etc.).

For practical usage today, treat `file-organizer/` as the runnable package root.

## Features (implemented)

- Local filesystem scanning (recursive).
- Optional GitHub scanning via `gh` CLI + local clone/pull.
- Optional Google Drive scanning via Drive API.
- Rule-based destination paths using templates.
- Category detection by extension.
- Naming templates (date/project/category/original name placeholders).
- Conflict handling: `skip`, `rename`, `prompt`, `keep_newest`, `keep_oldest`, `overwrite`.
- Copy or move operations.
- Transaction logging and `undo` for the last batch.
- Rich terminal output for scan/preview/history.

## Requirements

- Python 3.8+
- For GitHub source:
  - `gh` authenticated (`gh auth login`)
  - `git`
- For Google Drive source:
  - `google-api-python-client`
  - `google-auth-httplib2`
  - `google-auth-oauthlib`
  - OAuth credentials JSON

## Installation

From repository root:

```bash
pip install -r requirements.txt
pip install -e ./file-organizer
```

## CLI commands

```bash
file-organizer --help
```

The `file-organizer` executable is exposed via the package metadata entry point (`console_scripts`) in `file-organizer/setup.py`. If you want to rename the command or add aliases, update that entry and reinstall the package.

Available commands:

- `scan` — scan enabled sources and print counts/sizes
- `preview` — generate and display planned organization changes
- `organize` — execute plan (dry-run by default)
- `undo` — undo last logged operation batch
- `history` — show recent transactions
- `init-config` — create config file
- `show-config` — print loaded config

## Quick start

1. Initialize config:

```bash
file-organizer init-config
```

2. Edit config (default path: `~/.config/file-organizer/config.yaml`) and set at least:

- `organization.base_path`
- `sources.local.paths`

3. Scan and preview:

```bash
file-organizer scan
file-organizer preview
```

4. Execute when ready:

```bash
file-organizer organize --execute
```

## Configuration overview

Main sections:

- `organization`
  - `base_path`
  - `structure` (first template string is used)
  - `projects.patterns`
  - `categories`
  - `naming`
- `safety`
  - `mode`: `copy` or `move`
  - `create_backup`
  - `backup_path`
  - `dry_run_default`
  - `conflict_resolution`
  - `preserve_timestamps`
- `sources`
  - `local`
  - `github`
  - `google_drive`
- `logging`
  - `transaction_log`

### Template variables

Supported placeholders in `organization.structure` / naming templates:

- `{project}`
- `{category}`
- `{year}` `{month}` `{day}`
- `{filename}`
- `{original_name}`
- `{extension}`
- `{date}` (for naming template)

## Source-specific notes

### Local

- Scans configured files/directories recursively.
- `exclude_patterns` are matched against names and path strings.

### GitHub

- If `sources.github.repos` is empty, scanner requests up to 1000 repos from `gh repo list`.
- Repositories are cloned/pulled to `sources.github.clone_path`.

### Google Drive

- Scanner authenticates via OAuth and can recurse folder IDs.
- **Current behavior:** unified scanning calls Drive scan with `download=False`, so returned file paths are virtual local paths for most files and may not exist on disk during organization execution. In practice, Drive integration is reliable for inventory/preview, but execution may require code/config adjustments.

## Known limitations

- Repository layout is duplicated at root and `file-organizer/`, which can confuse imports/test discovery.
- Running `pytest` at repo root currently hits test-module name collisions (`test_basic.py` appears in both trees).
- GitHub scanner error handling has edge-case issues when `gh` is missing.

## Development

Temporary test command workaround (current duplicate-tree state):

```bash
pytest -q tests test_basic.py --ignore=file-organizer/test_basic.py
```

This ignore flag is only a stopgap while both project trees exist. A better long-term fix is to resolve duplicate test-module discovery (for example, via `pytest.ini`/`pyproject.toml` test path configuration or by unifying the repository into a single source tree).

## License

MIT (see `LICENSE`).
