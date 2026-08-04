"""Tests for spreadsheet loading."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from battery_allocation.data.spreadsheet import is_supported_data_file, read_spreadsheet


def test_is_supported_data_file(tmp_path: Path):
    csv_file = tmp_path / "fleet.csv"
    csv_file.write_text("a,b\n1,2\n", encoding="utf-8")
    assert is_supported_data_file(csv_file)
    assert not is_supported_data_file(tmp_path / "notes.txt")


def test_read_spreadsheet_csv(tmp_path: Path):
    path = tmp_path / "data.csv"
    path.write_text("battery_id,chemistry\nBAT-1,LFP\n", encoding="utf-8")
    df = read_spreadsheet(path)
    assert list(df.columns) == ["battery_id", "chemistry"]
    assert len(df) == 1


def test_read_spreadsheet_excel(tmp_path: Path):
    pytest.importorskip("openpyxl")
    path = tmp_path / "data.xlsx"
    pd.DataFrame({"battery_id": ["BAT-1"], "chemistry": ["LFP"]}).to_excel(path, index=False)
    df = read_spreadsheet(path)
    assert "battery_id" in df.columns


def test_read_spreadsheet_unsupported(tmp_path: Path):
    path = tmp_path / "data.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        read_spreadsheet(path)
