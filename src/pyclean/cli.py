from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from pyclean.cleaner import collect_cleanup_candidates, execute_cleanup
from pyclean.models import CleanupAction, CleanupCandidate, CleanupMode, FileEntry
from pyclean.scanner import scan_large_files
from pyclean.utils import configure_logging, dump_json, format_size, isoformat_utc, parse_size

app = typer.Typer(help="Safely scan and clean junk files.", no_args_is_help=True)
console = Console()


def _render_scan_table(entries: list[FileEntry]) -> None:
    table = Table(title="Large Files")
    table.add_column("Path")
    table.add_column("Size", justify="right")
    table.add_column("Modified")
    for entry in entries:
        table.add_row(str(entry.path), format_size(entry.size_bytes), isoformat_utc(entry.modified_at))
    console.print(table)


def _render_cleanup_table(actions: list[CleanupAction]) -> None:
    table = Table(title="Cleanup Actions")
    table.add_column("Status")
    table.add_column("Path")
    table.add_column("Reason")
    for action in actions:
        table.add_row(action.status, str(action.path), action.reason)
    console.print(table)


def _scan_to_json(entries: list[FileEntry], summary: dict[str, Any]) -> str:
    return dump_json(
        {
            "results": [
                {
                    "path": str(entry.path),
                    "size_bytes": entry.size_bytes,
                    "modified_at": isoformat_utc(entry.modified_at),
                }
                for entry in entries
            ],
            "summary": summary,
        }
    )


def _cleanup_to_json(candidates: list[CleanupCandidate], actions: list[CleanupAction], summary: dict[str, Any]) -> str:
    return dump_json(
        {
            "candidates": [
                {"path": str(candidate.path), "kind": candidate.kind, "size_bytes": candidate.size_bytes}
                for candidate in candidates
            ],
            "actions": [
                {"path": str(action.path), "status": action.status, "reason": action.reason}
                for action in actions
            ],
            "summary": summary,
        }
    )


@app.callback()
def main(
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable debug logging.")] = False,
) -> None:
    configure_logging(verbose=verbose)


@app.command("scan-large")
def scan_large(
    path: Annotated[Path, typer.Option("--path", exists=True, file_okay=False, dir_okay=True)] = Path.cwd(),
    min_size: Annotated[str, typer.Option("--min-size", help="Minimum file size, e.g. 100MB.")] = "100MB",
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="Maximum number of results.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
    exclude: Annotated[list[str], typer.Option("--exclude", help="Glob pattern to exclude.")] = [],
) -> None:
    try:
        entries, summary = scan_large_files(
            base_path=path,
            min_size_bytes=parse_size(min_size),
            limit=limit,
            exclude=tuple(exclude),
        )
    except (ValueError, FileNotFoundError, NotADirectoryError) as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    summary_payload = {
        "scanned_directories": summary.scanned_directories,
        "scanned_files": summary.scanned_files,
        "matches": summary.matches,
    }
    if json_output:
        console.print(_scan_to_json(entries, summary_payload))
        return
    _render_scan_table(entries)
    console.print(
        f"Scanned {summary.scanned_directories} directories and {summary.scanned_files} files; "
        f"found {summary.matches} matches."
    )


def _run_cleanup_command(
    mode: CleanupMode,
    path: Path | None,
    dry_run: bool,
    yes: bool,
    limit: int | None,
    json_output: bool,
    exclude: list[str],
) -> None:
    try:
        candidates = collect_cleanup_candidates(mode=mode, path=path, exclude=tuple(exclude))
        if limit is not None:
            candidates = candidates[:limit]
        actions, summary = execute_cleanup(
            mode=mode,
            candidates=candidates,
            dry_run=dry_run,
            confirmed=yes,
        )
    except ValueError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    summary_payload = {
        "mode": summary.mode,
        "dry_run": summary.dry_run,
        "deleted_count": summary.deleted_count,
        "skipped_count": summary.skipped_count,
        "error_count": summary.error_count,
    }
    if json_output:
        console.print(_cleanup_to_json(candidates, actions, summary_payload))
        return
    _render_cleanup_table(actions)
    console.print(
        f"{summary.mode} cleanup complete. deleted={summary.deleted_count} "
        f"skipped={summary.skipped_count} errors={summary.error_count}"
    )


@app.command("clean-temp")
def clean_temp(
    path: Annotated[Path | None, typer.Option("--path", help="Optional subpath inside safe temp roots.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run/--no-dry-run", help="Preview deletions.", show_default=True)] = True,
    yes: Annotated[bool, typer.Option("--yes", help="Required when using --no-dry-run.")] = False,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="Maximum number of candidates.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
    exclude: Annotated[list[str], typer.Option("--exclude", help="Glob pattern to exclude.")] = [],
) -> None:
    _run_cleanup_command("temp", path, dry_run, yes, limit, json_output, exclude)


@app.command("clean-cache")
def clean_cache(
    path: Annotated[Path | None, typer.Option("--path", help="Optional subpath inside safe cache roots.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run/--no-dry-run", help="Preview deletions.", show_default=True)] = True,
    yes: Annotated[bool, typer.Option("--yes", help="Required when using --no-dry-run.")] = False,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="Maximum number of candidates.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
    exclude: Annotated[list[str], typer.Option("--exclude", help="Glob pattern to exclude.")] = [],
) -> None:
    _run_cleanup_command("cache", path, dry_run, yes, limit, json_output, exclude)


if __name__ == "__main__":
    app()
