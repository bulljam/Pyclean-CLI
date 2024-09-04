from __future__ import annotations

from pathlib import Path

import pytest

from pyclean.scanner import scan_large_files
from pyclean.utils import parse_size


def write_file(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_scan_large_files_returns_sorted_matches(tmp_path: Path) -> None:
    write_file(tmp_path / "small.txt", 8)
    write_file(tmp_path / "large.bin", 128)
    write_file(tmp_path / "bigger.bin", 256)

    results, summary = scan_large_files(tmp_path, min_size_bytes=64, limit=2)

    assert [item.path.name for item in results] == ["bigger.bin", "large.bin"]
    assert summary.matches == 2
    assert summary.scanned_files == 3


def test_scan_large_files_respects_exclude_patterns(tmp_path: Path) -> None:
    write_file(tmp_path / "keep.bin", 128)
    write_file(tmp_path / "cache" / "skip.bin", 256)

    results, _ = scan_large_files(tmp_path, min_size_bytes=64, exclude=("cache*",))

    assert [item.path.name for item in results] == ["keep.bin"]


def test_scan_large_files_ignores_symlinks_by_default(tmp_path: Path) -> None:
    target = tmp_path / "target.bin"
    target.write_bytes(b"x" * 128)
    link = tmp_path / "linked.bin"
    link.symlink_to(target)

    results, summary = scan_large_files(tmp_path, min_size_bytes=64)

    assert [item.path.name for item in results] == ["target.bin"]
    assert summary.scanned_files == 1


def test_parse_size_supports_human_units() -> None:
    assert parse_size("1kb") == 1024
    assert parse_size("1.5MB") == int(1.5 * 1024**2)


def test_scan_large_files_raises_for_missing_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        scan_large_files(tmp_path / "missing", min_size_bytes=1)
