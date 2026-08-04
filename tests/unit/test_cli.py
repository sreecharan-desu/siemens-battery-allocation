"""Tests for CLI commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from battery_allocation.cli.main import app

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "1.2.0" in result.stdout


def test_run_with_sample(project_root: Path):
    result = runner.invoke(app, ["run", "--sample", "--skip-viz", "-o", str(project_root / "outputs")])
    assert result.exit_code == 0
    assert "Pipeline completed" in result.stdout or "vehicles_served" in result.stdout


def test_run_json_output(project_root: Path, tmp_path: Path):
    result = runner.invoke(
        app,
        ["run", "--sample", "--skip-viz", "--json", "-o", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "proposed_metrics" in result.stdout


def test_upload_command(project_root: Path, tmp_path: Path):
    src = tmp_path / "upload_test.csv"
    src.write_text("battery_id\nBAT-1\n", encoding="utf-8")
    result = runner.invoke(app, ["upload", str(src)])
    assert result.exit_code == 0
    assert "Uploaded" in result.stdout


def test_files_command(project_root: Path):
    result = runner.invoke(app, ["files"])
    assert result.exit_code == 0


def test_validate_sample(project_root: Path):
    result = runner.invoke(app, ["validate", "--sample"])
    assert result.exit_code == 0
    assert "200 batteries" in result.stdout
    assert "50" in result.stdout
