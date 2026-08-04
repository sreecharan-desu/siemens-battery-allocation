"""Pydantic schemas for CSV row validation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class BatteryRow(BaseModel):
    battery_id: str
    chemistry: str
    nominal_voltage_V: float = Field(gt=0)
    rated_capacity_Ah: float = Field(gt=0)
    state_of_charge_percent: float = Field(ge=0, le=100)
    state_of_health_percent: float = Field(ge=0, le=100)
    temperature_C: float
    internal_resistance_mOhm: float = Field(gt=0)
    cycle_count: int = Field(ge=0)
    age_years: float = Field(ge=0)
    cell_voltage_imbalance_mV: float = Field(ge=0)
    max_temperature_last_24h_C: float
    estimated_available_energy_kWh: float = Field(ge=0)
    station_status: str

    @field_validator("battery_id", "chemistry", "station_status")
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        return value.strip()


class VehicleRequestRow(BaseModel):
    request_id: str
    arrival_time: str
    vehicle_type: str
    required_range_km: float = Field(gt=0)
    load_category: str
    priority: str
    minimum_acceptable_SOC_percent: float = Field(ge=0, le=100)
    maximum_wait_time_min: int = Field(ge=0)

    @field_validator("request_id", "vehicle_type", "load_category", "priority")
    @classmethod
    def _strip_strings(cls, value: str) -> str:
        return value.strip()

    def parsed_arrival_time(self) -> datetime:
        return datetime.strptime(self.arrival_time.strip(), "%Y-%m-%d %H:%M:%S")
