"""Tests for twist handler and API error paths."""

from __future__ import annotations

from fastapi.testclient import TestClient

from battery_allocation.api.app import create_app
from battery_allocation.core.models import Battery
from battery_allocation.core.twist import TwistContext, apply_twist_filters, from_dict


def test_from_dict_parses_optional_fields():
    ctx = from_dict({"name": "heat_wave", "min_soh_percent": 75, "max_temperature_c": 40})
    assert ctx.name == "heat_wave"
    assert ctx.min_soh_percent == 75.0
    assert ctx.max_temperature_c == 40.0


def test_apply_twist_filters(sample_battery: Battery):
    twist = TwistContext(name="filter", min_soh_percent=80.0)
    batteries = [
        sample_battery,
        Battery(**{**sample_battery.__dict__, "battery_id": "BAT-LOW", "state_of_health_percent": 70.0}),
    ]
    filtered, _ = apply_twist_filters(twist, batteries, [])
    assert len(filtered) == 1
    assert filtered[0].battery_id == "BAT-TEST"


def test_pipeline_run_api_with_skip_viz():
    client = TestClient(create_app())
    response = client.post("/pipeline/run", json={"skip_visualizations": True})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["violations"] == []


def test_pipeline_run_api_invalid_csv(tmp_path):
    client = TestClient(create_app())
    bad_csv = tmp_path / "missing.csv"
    response = client.post("/pipeline/run", json={"battery_csv": str(bad_csv)})
    assert response.status_code == 400


def test_setup_logging():
    from battery_allocation.utils.logging import setup_logging

    setup_logging("DEBUG", "json")
    setup_logging("INFO", "text")
