"""Integration tests for pipeline and API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from battery_allocation.api.app import create_app
from battery_allocation.config.settings import get_settings
from battery_allocation.pipeline.runner import run_pipeline


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_classifications_summary(client: TestClient):
    response = client.get("/classifications/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_batteries"] == 200
    assert "by_category" in data


def test_pipeline_run_integration(tmp_path: Path):
    settings = get_settings()
    result = run_pipeline(
        battery_csv=settings.resolved_battery_csv(),
        vehicle_csv=settings.resolved_vehicle_csv(),
        output_dir=tmp_path,
        skip_visualizations=True,
    )
    assert result.violations_proposed == []
    assert result.violations_baseline == []
    assert (tmp_path / "battery_classifications.csv").exists()
    assert (tmp_path / "metrics_report.json").exists()
