"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from battery_allocation.core.models import Battery, VehiclePriority, VehicleRequest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Repository root (contains pyproject.toml and data/)."""
    root = Path(__file__).resolve().parents[1]
    assert (root / "pyproject.toml").is_file()
    assert (root / "data").is_dir()
    return root


@pytest.fixture
def sample_battery() -> Battery:
    return Battery(
        battery_id="BAT-TEST",
        chemistry="LFP",
        nominal_voltage_v=48.0,
        rated_capacity_ah=40.0,
        state_of_charge_percent=80.0,
        state_of_health_percent=85.0,
        temperature_c=30.0,
        internal_resistance_mohm=50.0,
        cycle_count=500,
        age_years=2.0,
        cell_voltage_imbalance_mv=30.0,
        max_temperature_last_24h_c=35.0,
        estimated_available_energy_kwh=1.2,
        station_status="AVAILABLE",
    )


@pytest.fixture
def sample_request() -> VehicleRequest:
    return VehicleRequest(
        request_id="REQ-TEST",
        arrival_time=datetime(2026, 7, 1, 8, 0, 0),
        vehicle_type="Personal Commuter",
        required_range_km=30.0,
        load_category="Light",
        priority=VehiclePriority.HIGH,
        minimum_acceptable_soc_percent=30.0,
        maximum_wait_time_min=10,
    )
