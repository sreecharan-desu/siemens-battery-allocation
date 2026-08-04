"""Load CSV or Excel spreadsheets into pandas DataFrames."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def is_supported_data_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS and path.is_file()


def read_spreadsheet(path: Path, sheet: str | int | None = 0) -> pd.DataFrame:
    """Read a CSV or Excel file into a DataFrame."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
    raise ValueError(f"Unsupported file type: {suffix}. Use CSV or Excel (.xlsx, .xls).")
