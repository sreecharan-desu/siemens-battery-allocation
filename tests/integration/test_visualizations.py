"""Integration test with visualizations enabled."""

from __future__ import annotations

from pathlib import Path

from battery_allocation.config.settings import get_settings
from battery_allocation.pipeline.runner import run_pipeline


def test_pipeline_generates_visualizations(tmp_path: Path):
    settings = get_settings()
    result = run_pipeline(
        battery_csv=settings.resolved_battery_csv(),
        vehicle_csv=settings.resolved_vehicle_csv(),
        output_dir=tmp_path,
        skip_visualizations=False,
    )
    assert any(str(p).endswith(".png") for p in result.output_paths)
    assert (tmp_path / "quarantine_report.csv").exists()
