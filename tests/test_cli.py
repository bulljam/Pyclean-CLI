from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pyclean.cli import app

runner = CliRunner()


def test_scan_large_json_output(tmp_path: Path) -> None:
    large_file = tmp_path / "large.bin"
    large_file.write_bytes(b"x" * 128)

    result = runner.invoke(
        app,
        ["scan-large", "--path", str(tmp_path), "--min-size", "64", "--json"],
    )

    assert result.exit_code == 0
    assert '"matches": 1' in result.stdout
    assert str(large_file) in result.stdout


def test_clean_temp_defaults_to_dry_run(tmp_path: Path, monkeypatch) -> None:
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    candidate = temp_root / "file.tmp"
    candidate.write_text("x")
    monkeypatch.setenv("TMPDIR", str(temp_root))

    result = runner.invoke(app, ["clean-temp", "--path", str(temp_root), "--json"])

    assert result.exit_code == 0
    assert '"dry_run": true' in result.stdout
    assert candidate.exists()


def test_clean_temp_requires_yes_for_real_deletion(tmp_path: Path, monkeypatch) -> None:
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    (temp_root / "file.tmp").write_text("x")
    monkeypatch.setenv("TMPDIR", str(temp_root))

    result = runner.invoke(app, ["clean-temp", "--path", str(temp_root), "--no-dry-run"])

    assert result.exit_code != 0
    assert "real deletion requires --yes" in result.stdout
