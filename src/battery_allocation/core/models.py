"""Domain models for batteries, requests, classifications, and allocations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from battery_allocation.config.settings import get_thresholds


class BatteryCategory(StrEnum):
    SAFE_AVAILABLE = "Safe and Available"
    DEGRADED_USABLE = "Degraded but Usable"
    UNSAFE_QUARANTINE = "Unsafe / Quarantine"


class VehiclePriority(StrEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    NORMAL = "Normal"

    @property
    def weight(self) -> int:
        return {VehiclePriority.CRITICAL: 3, VehiclePriority.HIGH: 2, VehiclePriority.NORMAL: 1}[
            self
        ]


@dataclass(frozen=True)
class Battery:
    battery_id: str
    chemistry: str
    nominal_voltage_v: float
    rated_capacity_ah: float
    state_of_charge_percent: float
    state_of_health_percent: float
    temperature_c: float
    internal_resistance_mohm: float
    cycle_count: int
    age_years: float
    cell_voltage_imbalance_mv: float
    max_temperature_last_24h_c: float
    estimated_available_energy_kwh: float
    station_status: str

    @property
    def is_station_available(self) -> bool:
        return self.station_status.strip().upper() == "AVAILABLE"


@dataclass(frozen=True)
class VehicleRequest:
    request_id: str
    arrival_time: datetime
    vehicle_type: str
    required_range_km: float
    load_category: str
    priority: VehiclePriority
    minimum_acceptable_soc_percent: float
    maximum_wait_time_min: int

    @property
    def required_energy_kwh(self) -> float:
        thresholds = get_thresholds()
        factor = float(thresholds.vehicle_energy_kwh_per_km.get(self.vehicle_type, 0.022))
        load_multiplier = float(thresholds.load_multipliers.get(self.load_category, 1.0))
        return self.required_range_km * factor * load_multiplier


@dataclass
class BatteryClassification:
    battery_id: str
    category: BatteryCategory
    suitability_score: float
    reasons: list[str]


@dataclass
class Allocation:
    request_id: str
    battery_id: str | None
    served: bool
    reason: str = ""


@dataclass
class PipelineResult:
    classifications: dict[str, BatteryClassification]
    proposed_allocations: list[Allocation]
    baseline_allocations: list[Allocation]
    proposed_metrics: dict[str, object]
    baseline_metrics: dict[str, object]
    violations_proposed: list[str]
    violations_baseline: list[str]
    output_paths: list[str]
