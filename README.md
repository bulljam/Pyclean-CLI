# pyclean

`pyclean` is a safety-first Python CLI for scanning large files and cleaning disposable temp/cache data on a local machine.

The project is built for Python 3.11+, uses `Typer` for the CLI, `Rich` for terminal output, `pathlib` for filesystem work, and `pytest` for automated tests.

## Features

- `pyclean scan-large`: find files above a configurable size threshold.
- `pyclean clean-temp`: preview or remove files from safe temp directories.
- `pyclean clean-cache`: preview or remove files from safe cache directories.
- Dry-run is the default for destructive commands.
- JSON output is available for automation.
- Exclusion globs let you protect specific files or directories.

## Tech Stack

- Python 3.11+
- Typer for the CLI
- Rich for terminal rendering
- `pathlib` for filesystem paths
- `pytest` for automated tests
- `setuptools` with a `src/` layout for packaging

## Project Structure

```text
pyclean/
├── src/pyclean/
│   ├── __init__.py
│   ├── cleaner.py
│   ├── cli.py
│   ├── models.py
│   ├── rules.py
│   ├── scanner.py
│   └── utils.py
├── tests/
├── pyproject.toml
├── .gitignore
└── README.md
```

## Local Setup

Always work inside the project-local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Development Commands

Run tests:

```bash
.venv/bin/pytest
```

Run the CLI directly from the virtual environment:

```bash
.venv/bin/pyclean --help
```

Or through Python:

```bash
.venv/bin/python -m pyclean.cli --help
```

## Usage Examples

Scan for files larger than 500 MB:

```bash
.venv/bin/pyclean scan-large --path ~/Downloads --min-size 500MB --limit 20
```

Scan and emit JSON:

```bash
.venv/bin/pyclean scan-large --path . --min-size 50MB --json
```

Preview temp cleanup without deleting anything:

```bash
.venv/bin/pyclean clean-temp --dry-run
```

Preview cache cleanup for a specific cache directory:

```bash
.venv/bin/pyclean clean-cache --path ~/.cache --exclude "pip*" --json
```

Perform real deletion only after explicit confirmation:

```bash
.venv/bin/pyclean clean-temp --path /tmp/my-safe-temp --no-dry-run --yes
```

## Architecture

The code is split into small layers so the safety model stays centralized:

- `models.py` holds typed dataclasses used across the app.
- `rules.py` contains the allowlist and dangerous-path checks.
- `scanner.py` handles large-file discovery with exclusion support and no symlink following by default.
- `cleaner.py` collects safe cleanup candidates and executes dry-run or confirmed deletion.
- `cli.py` exposes the Typer commands and Rich/JSON output formats.
- `utils.py` provides shared helpers like size parsing, formatting, and logging setup.

## Safety Model

Safety is enforced in several places:

- Dry-run is enabled by default for `clean-temp` and `clean-cache`.
- Real deletion requires both `--no-dry-run` and `--yes`.
- Cleanup commands validate paths against a strict allowlist of safe temp/cache roots.
- Dangerous paths such as `/`, drive/system roots, and the user home directory are blocked.
- Symlinks are skipped by default.
- Exclusion globs apply before deletion.
- Permission errors are caught, logged, and reported instead of aborting the whole run.

## Testing

The test suite uses `tmp_path` fixtures only. It does not touch real system files.

Covered behaviors include:

- large file scanning
- dry-run behavior
- real deletion behavior
- exclusion rules
- cleanup error handling
- CLI JSON output and confirmation enforcement
