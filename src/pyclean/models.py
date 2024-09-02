from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

CleanupMode = Literal["temp", "cache"]
ActionStatus = Literal["deleted", "would_delete", "skipped", "error"]


@dataclass(slots=True, frozen=True)
class FileEntry:
    path: Path
    size_bytes: int
    modified_at: datetime


@dataclass(slots=True, frozen=True)
class CleanupCandidate:
    path: Path
    kind: Literal["file", "directory"]
    size_bytes: int | None = None


@dataclass(slots=True, frozen=True)
class CleanupAction:
    path: Path
    status: ActionStatus
    reason: str


@dataclass(slots=True, frozen=True)
class ScanSummary:
    scanned_directories: int
    scanned_files: int
    matches: int


@dataclass(slots=True, frozen=True)
class CleanupSummary:
    mode: CleanupMode
    dry_run: bool
    deleted_count: int
    skipped_count: int
    error_count: int
