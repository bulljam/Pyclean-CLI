from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from pyclean.cleaner import collect_cleanup_candidates, execute_cleanup


def test_collect_cleanup_candidates_uses_safe_temp_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    temp_root = tmp_path / "temp-root"
    temp_root.mkdir()
    (temp_root / "a.tmp").write_text("x")
    (temp_root / "nested").mkdir()

    monkeypatch.setenv("TMPDIR", str(temp_root))

    candidates = collect_cleanup_candidates(mode="temp", path=temp_root)

    assert [candidate.path.name for candidate in candidates] == ["a.tmp", "nested"]


def test_collect_cleanup_candidates_blocks_dangerous_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        collect_cleanup_candidates(mode="temp", path=Path("/"))


def test_dry_run_does_not_delete_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_root = tmp_path / ".cache"
    cache_root.mkdir()
    victim = cache_root / "artifact.bin"
    victim.write_text("hello")
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_root))

    candidates = collect_cleanup_candidates(mode="cache", path=cache_root)
    actions, summary = execute_cleanup(mode="cache", candidates=candidates, dry_run=True)

    assert victim.exists()
    assert actions[0].status == "would_delete"
    assert summary.deleted_count == 0
    assert summary.skipped_count == 1


def test_real_delete_requires_yes_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    (temp_root / "victim.tmp").write_text("x")
    monkeypatch.setenv("TMPDIR", str(temp_root))

    candidates = collect_cleanup_candidates(mode="temp", path=temp_root)

    with pytest.raises(ValueError):
        execute_cleanup(mode="temp", candidates=candidates, dry_run=False, confirmed=False)


def test_execute_cleanup_deletes_files_and_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    file_path = temp_root / "victim.tmp"
    file_path.write_text("x")
    directory_path = temp_root / "folder"
    directory_path.mkdir()
    (directory_path / "inner.tmp").write_text("x")
    monkeypatch.setenv("TMPDIR", str(temp_root))

    candidates = collect_cleanup_candidates(mode="temp", path=temp_root)
    actions, summary = execute_cleanup(mode="temp", candidates=candidates, dry_run=False, confirmed=True)

    assert not file_path.exists()
    assert not directory_path.exists()
    assert summary.deleted_count == 2
    assert {action.status for action in actions} == {"deleted"}


def test_collect_cleanup_candidates_respects_exclude_patterns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    (temp_root / "keep.tmp").write_text("x")
    (temp_root / "skip.tmp").write_text("x")
    monkeypatch.setenv("TMPDIR", str(temp_root))

    candidates = collect_cleanup_candidates(mode="temp", path=temp_root, exclude=("skip*",))

    assert [candidate.path.name for candidate in candidates] == ["keep.tmp"]


def test_execute_cleanup_records_delete_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    victim = temp_root / "victim.tmp"
    victim.write_text("x")
    monkeypatch.setenv("TMPDIR", str(temp_root))
    candidates = collect_cleanup_candidates(mode="temp", path=temp_root)

    with patch.object(Path, "unlink", side_effect=PermissionError("denied")):
        actions, summary = execute_cleanup(
            mode="temp",
            candidates=candidates,
            dry_run=False,
            confirmed=True,
        )

    assert actions[0].status == "error"
    assert summary.error_count == 1
