"""Battery suitability scoring (0–100) from health parameters."""

from __future__ import annotations

from battery_allocation.core.models import Battery


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def compute_suitability_score(battery: Battery) -> float:
    """Composite score from SOH, SOC, resistance, imbalance, and temperature."""
    soh_score = (battery.state_of_health_percent / 100.0) * 30.0
    soc_score = (battery.state_of_charge_percent / 100.0) * 25.0
    resistance_score = _clamp((90.0 - battery.internal_resistance_mohm) / 57.0 * 20.0)
    imbalance_score = _clamp((100.0 - battery.cell_voltage_imbalance_mv) / 94.0 * 15.0)

    temp = battery.temperature_c
    if 25.0 <= temp <= 35.0:
        temp_score = 10.0
    elif temp < 25.0:
        temp_score = _clamp(10.0 - (25.0 - temp) * 0.4)
    else:
        temp_score = _clamp(10.0 - (temp - 35.0) * 0.5)

    total = soh_score + soc_score + resistance_score + imbalance_score + temp_score
    return round(_clamp(total), 2)
