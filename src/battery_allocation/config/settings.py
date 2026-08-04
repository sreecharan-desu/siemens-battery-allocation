"""Application settings and YAML configuration loading."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


class ThresholdConfig:
    """Classification and energy-model thresholds loaded from YAML."""

    def __init__(self, data: dict[str, Any]) -> None:
        unsafe = data.get("unsafe", {})
        degraded = data.get("degraded", {})
        self.unsafe_soh = float(unsafe.get("soh_percent", 60.0))
        self.unsafe_temp = float(unsafe.get("temperature_c", 45.0))
        self.unsafe_resistance = float(unsafe.get("internal_resistance_mohm", 85.0))
        self.unsafe_imbalance = float(unsafe.get("cell_voltage_imbalance_mv", 90.0))
        self.unsafe_max_temp_24h = float(unsafe.get("max_temperature_last_24h_c", 50.0))
        self.degraded_soh = float(degraded.get("soh_percent", 70.0))
        self.degraded_resistance = float(degraded.get("internal_resistance_mohm", 70.0))
        self.degraded_imbalance = float(degraded.get("cell_voltage_imbalance_mv", 60.0))
        self.degraded_cycle_count = int(degraded.get("cycle_count", 1400))
        self.vehicle_energy_kwh_per_km = dict(
            data.get(
                "vehicle_energy_kwh_per_km",
                {
                    "Personal Commuter": 0.020,
                    "Delivery Two-Wheeler": 0.025,
                    "Campus Utility EV": 0.022,
                },
            )
        )
        self.load_multipliers = dict(
            data.get("load_multipliers", {"Light": 1.0, "Medium": 1.1, "Heavy": 1.2})
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BATTERY_ALLOCATION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_root: Path = Field(default_factory=_project_root)
    config_dir: Path | None = None
    battery_csv: Path | None = None
    vehicle_csv: Path | None = None
    output_dir: Path | None = None
    log_level: str = "INFO"
    log_format: str = "text"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    mpl_config_dir: Path | None = None

    @field_validator(
        "project_root",
        "config_dir",
        "battery_csv",
        "vehicle_csv",
        "output_dir",
        "mpl_config_dir",
        mode="before",
    )
    @classmethod
    def _coerce_path(cls, value: Any) -> Path | None:
        if value is None or value == "":
            return None
        return Path(value)

    def resolved_config_dir(self) -> Path:
        return self.config_dir or self.project_root / "config"

    def resolved_battery_csv(self) -> Path:
        return self.battery_csv or self.project_root / "data" / "Problem_1_Battery_Fleet_200_Packs.csv"

    def resolved_vehicle_csv(self) -> Path:
        return self.vehicle_csv or self.project_root / "data" / "Problem_1_Vehicle_Demand_50_Requests.csv"

    def resolved_output_dir(self) -> Path:
        return self.output_dir or self.project_root / "outputs"

    def resolved_mpl_config_dir(self) -> Path:
        return self.mpl_config_dir or self.project_root / ".matplotlib"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


@lru_cache
def get_thresholds() -> ThresholdConfig:
    settings = get_settings()
    path = settings.resolved_config_dir() / "thresholds.yaml"
    if not path.exists():
        return ThresholdConfig({})
    return ThresholdConfig(load_yaml(path))


@lru_cache
def get_pipeline_config() -> dict[str, Any]:
    settings = get_settings()
    path = settings.resolved_config_dir() / "default.yaml"
    if not path.exists():
        return {}
    return load_yaml(path)
