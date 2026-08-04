"""Tests for dynamic data file discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from battery_allocation.data.discovery import (
    copy_upload,
    discover_files,
    guess_battery_files,
    load_user_config,
    resolve_data_file,
    save_user_config,
)


def test_discover_files_finds_csv_in_data(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "fleet.csv").write_text("a\n1\n", encoding="utf-8")
    files = discover_files(tmp_path)
    assert any(f.name == "fleet.csv" for f in files)


def test_guess_battery_files_scores_hints(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "random.csv").write_text("a\n1\n", encoding="utf-8")
    (data_dir / "battery_fleet.csv").write_text("a\n1\n", encoding="utf-8")
    guesses = guess_battery_files(tmp_path)
    assert guesses[0].name == "battery_fleet.csv"


def test_resolve_explicit_path(tmp_path: Path):
    path = tmp_path / "custom.csv"
    path.write_text("x\n1\n", encoding="utf-8")
    resolved = resolve_data_file(tmp_path, "battery", explicit=path)
    assert resolved == path.resolve()


def test_resolve_use_sample(project_root: Path):
    battery = resolve_data_file(project_root, "battery", use_sample=True)
    vehicle = resolve_data_file(project_root, "vehicle", use_sample=True)
    assert battery.exists()
    assert vehicle.exists()


def test_save_and_load_user_config(tmp_path: Path):
    battery = tmp_path / "b.csv"
    vehicle = tmp_path / "v.csv"
    battery.write_text("a\n1\n", encoding="utf-8")
    vehicle.write_text("a\n1\n", encoding="utf-8")
    save_user_config(tmp_path, battery, vehicle)
    cfg = load_user_config(tmp_path)
    assert cfg["battery_file"] == str(battery.resolve())
    assert cfg["vehicle_file"] == str(vehicle.resolve())


def test_copy_upload(tmp_path: Path):
    src = tmp_path / "my fleet.csv"
    src.write_text("battery_id\nBAT-1\n", encoding="utf-8")
    dest = copy_upload(src, tmp_path)
    assert dest.exists()
    assert dest.parent.name == "uploads"


def test_copy_upload_rejects_unsupported(tmp_path: Path):
    src = tmp_path / "notes.txt"
    src.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        copy_upload(src, tmp_path)


def test_resolve_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="No battery"):
        resolve_data_file(tmp_path, "battery")
