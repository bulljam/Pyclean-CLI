from __future__ import annotations

import logging
import shutil
from pathlib import Path

from pyclean.models import CleanupAction, CleanupCandidate, CleanupMode, CleanupSummary
from pyclean.rules import allowed_roots_for_mode, resolve_path, should_exclude, validate_cleanup_root

logger = logging.getLogger("pyclean.cleaner")


def collect_cleanup_candidates(
    mode: CleanupMode,
    path: Path | None = None,
    exclude: tuple[str, ...] = (),
    follow_symlinks: bool = False,
) -> list[CleanupCandidate]:
    roots = [validate_cleanup_root(path, mode)] if path else list(allowed_roots_for_mode(mode))
    candidates: list[CleanupCandidate] = []

    for root in roots:
        if not root.exists():
            logger.debug("Skipping missing cleanup root: %s", root)
            continue

        for entry in root.iterdir():
            if should_exclude(entry, exclude):
                logger.info("Skipping excluded path: %s", entry)
                continue
            if entry.is_symlink():
                logger.info("Skipping symlink: %s", entry)
                if not follow_symlinks:
                    continue
            try:
                kind = "directory" if entry.is_dir() else "file"
                size_bytes = entry.stat(follow_symlinks=follow_symlinks).st_size if entry.is_file() else None
            except OSError as exc:
                logger.warning("Skipping unreadable path %s: %s", entry, exc)
                continue
            candidates.append(CleanupCandidate(path=entry, kind=kind, size_bytes=size_bytes))

    candidates.sort(key=lambda item: item.path.as_posix())
    return candidates


def execute_cleanup(
    mode: CleanupMode,
    candidates: list[CleanupCandidate],
    dry_run: bool = True,
    confirmed: bool = False,
) -> tuple[list[CleanupAction], CleanupSummary]:
    if not dry_run and not confirmed:
        raise ValueError("real deletion requires --yes")

    actions: list[CleanupAction] = []
    deleted_count = 0
    skipped_count = 0
    error_count = 0

    for candidate in candidates:
        if dry_run:
            actions.append(
                CleanupAction(
                    path=candidate.path,
                    status="would_delete",
                    reason=f"{mode} cleanup dry-run",
                )
            )
            skipped_count += 1
            continue

        try:
            if candidate.kind == "directory":
                shutil.rmtree(candidate.path)
            else:
                candidate.path.unlink()
            logger.info("Deleted %s", candidate.path)
            actions.append(CleanupAction(path=candidate.path, status="deleted", reason=mode))
            deleted_count += 1
        except OSError as exc:
            logger.warning("Failed deleting %s: %s", candidate.path, exc)
            actions.append(CleanupAction(path=candidate.path, status="error", reason=str(exc)))
            error_count += 1

    return actions, CleanupSummary(
        mode=mode,
        dry_run=dry_run,
        deleted_count=deleted_count,
        skipped_count=skipped_count,
        error_count=error_count,
    )
