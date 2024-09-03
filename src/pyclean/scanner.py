from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from pyclean.models import FileEntry, ScanSummary
from pyclean.rules import resolve_path, should_exclude

logger = logging.getLogger("pyclean.scanner")


def scan_large_files(
    base_path: Path,
    min_size_bytes: int,
    limit: int | None = None,
    exclude: tuple[str, ...] = (),
    follow_symlinks: bool = False,
) -> tuple[list[FileEntry], ScanSummary]:
    resolved_base = resolve_path(base_path)
    if not resolved_base.exists():
        raise FileNotFoundError(f"path does not exist: {resolved_base}")
    if not resolved_base.is_dir():
        raise NotADirectoryError(f"path is not a directory: {resolved_base}")

    matches: list[FileEntry] = []
    scanned_directories = 0
    scanned_files = 0

    for current_root, dirnames, filenames in os.walk(
        resolved_base, topdown=True, followlinks=follow_symlinks
    ):
        current_path = Path(current_root)
        scanned_directories += 1
        dirnames[:] = [
            name
            for name in dirnames
            if not should_exclude(current_path / name, exclude)
            and not ((current_path / name).is_symlink() and not follow_symlinks)
        ]

        for filename in filenames:
            file_path = current_path / filename
            if should_exclude(file_path, exclude):
                continue
            if file_path.is_symlink() and not follow_symlinks:
                logger.debug("Skipping symlink: %s", file_path)
                continue
            try:
                stat_result = file_path.stat(follow_symlinks=follow_symlinks)
            except OSError as exc:
                logger.warning("Skipping unreadable file %s: %s", file_path, exc)
                continue

            scanned_files += 1
            if stat_result.st_size < min_size_bytes:
                continue

            matches.append(
                FileEntry(
                    path=file_path,
                    size_bytes=stat_result.st_size,
                    modified_at=datetime.fromtimestamp(stat_result.st_mtime),
                )
            )

    matches.sort(key=lambda item: item.size_bytes, reverse=True)
    if limit is not None:
        matches = matches[:limit]

    return matches, ScanSummary(
        scanned_directories=scanned_directories,
        scanned_files=scanned_files,
        matches=len(matches),
    )
