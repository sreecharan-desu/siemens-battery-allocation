"""Load and validate battery fleet and vehicle demand datasets."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from battery_allocation.config.settings import get_settings
from battery_allocation.core.models import Battery, VehiclePriority, VehicleRequest
from battery_allocation.data.schemas import BatteryRow, VehicleRequestRow

logger = logging.getLogger(__name__)

BATTERY_COLUMNS = [
    "battery_id", "chemistry", "nominal_voltage_V", "rated_capacity_Ah",
    "state_of_charge_percent", "state_of_health_percent", "temperature_C",
    "internal_resistance_mOhm", "cycle_count", "age_years",
    "cell_voltage_imbalance_mV", "max_temperature_last_24h_C",
    "estimated_available_energy_kWh", "station_status",
]

VEHICLE_COLUMNS = [
    "request_id", "arrival_time", "vehicle_type", "required_range_km",
    "load_category", "priority", "minimum_acceptable_SOC_percent",
    "maximum_wait_time_min",
]


class DataLoadError(Exception):
    """Raised when dataset loading or validation fails."""


def _validate_columns(df: pd.DataFrame, required: list[str], path: Path) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataLoadError(f"Missing columns in {path}: {missing}")


def load_batteries(path: Path | None = None) -> list[Battery]:
    settings = get_settings()
    csv_path = path or settings.resolved_battery_csv()
    if not csv_path.exists():
        raise DataLoadError(f"Battery CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    _validate_columns(df, BATTERY_COLUMNS, csv_path)

    batteries: list[Battery] = []
    for idx, row in df.iterrows():
        try:
            row_dict = {str(k): v for k, v in row.to_dict().items()}
            validated = BatteryRow(**row_dict)
        except ValidationError as exc:
            raise DataLoadError(f"Invalid battery row {idx} in {csv_path}: {exc}") from exc

        batteries.append(
            Battery(
                battery_id=validated.battery_id,
                chemistry=validated.chemistry,
                nominal_voltage_v=validated.nominal_voltage_V,
                rated_capacity_ah=validated.rated_capacity_Ah,
                state_of_charge_percent=validated.state_of_charge_percent,
                state_of_health_percent=validated.state_of_health_percent,
                temperature_c=validated.temperature_C,
                internal_resistance_mohm=validated.internal_resistance_mOhm,
                cycle_count=validated.cycle_count,
                age_years=validated.age_years,
                cell_voltage_imbalance_mv=validated.cell_voltage_imbalance_mV,
                max_temperature_last_24h_c=validated.max_temperature_last_24h_C,
                estimated_available_energy_kwh=validated.estimated_available_energy_kWh,
                station_status=validated.station_status,
            )
        )

    logger.info("Loaded %d batteries from %s", len(batteries), csv_path)
    return batteries


def load_vehicle_requests(path: Path | None = None) -> list[VehicleRequest]:
    settings = get_settings()
    csv_path = path or settings.resolved_vehicle_csv()
    if not csv_path.exists():
        raise DataLoadError(f"Vehicle CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    _validate_columns(df, VEHICLE_COLUMNS, csv_path)

    requests: list[VehicleRequest] = []
    for idx, row in df.iterrows():
        try:
            row_dict = {str(k): v for k, v in row.to_dict().items()}
            validated = VehicleRequestRow(**row_dict)
            priority = VehiclePriority(validated.priority)
        except (ValidationError, ValueError) as exc:
            raise DataLoadError(f"Invalid vehicle row {idx} in {csv_path}: {exc}") from exc

        requests.append(
            VehicleRequest(
                request_id=validated.request_id,
                arrival_time=validated.parsed_arrival_time(),
                vehicle_type=validated.vehicle_type,
                required_range_km=validated.required_range_km,
                load_category=validated.load_category,
                priority=priority,
                minimum_acceptable_soc_percent=validated.minimum_acceptable_SOC_percent,
                maximum_wait_time_min=validated.maximum_wait_time_min,
            )
        )

    logger.info("Loaded %d vehicle requests from %s", len(requests), csv_path)
    return requests
