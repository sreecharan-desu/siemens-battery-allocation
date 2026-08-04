"""Battery health classification logic."""

from __future__ import annotations

from battery_allocation.config.settings import ThresholdConfig, get_thresholds
from battery_allocation.core.models import Battery, BatteryCategory, BatteryClassification
from battery_allocation.core.scoring import compute_suitability_score


def classify_battery(
    battery: Battery,
    thresholds: ThresholdConfig | None = None,
) -> BatteryClassification:
    """Classify a battery into exactly one category."""
    t = thresholds or get_thresholds()
    reasons: list[str] = []
    status = battery.station_status.strip().upper()

    if status == "REVIEW/QUARANTINE":
        reasons.append("Station status: REVIEW/QUARANTINE")
    if battery.state_of_health_percent < t.unsafe_soh:
        reasons.append(f"SOH below {t.unsafe_soh}%")
    if battery.temperature_c > t.unsafe_temp:
        reasons.append(f"Temperature above {t.unsafe_temp}°C")
    if battery.internal_resistance_mohm > t.unsafe_resistance:
        reasons.append(f"Internal resistance above {t.unsafe_resistance} mΩ")
    if battery.cell_voltage_imbalance_mv > t.unsafe_imbalance:
        reasons.append(f"Cell imbalance above {t.unsafe_imbalance} mV")
    if battery.max_temperature_last_24h_c > t.unsafe_max_temp_24h:
        reasons.append(f"24h max temperature above {t.unsafe_max_temp_24h}°C")

    score = compute_suitability_score(battery)
    if reasons:
        return BatteryClassification(
            battery_id=battery.battery_id,
            category=BatteryCategory.UNSAFE_QUARANTINE,
            suitability_score=score,
            reasons=reasons,
        )

    degraded_reasons: list[str] = []
    if battery.state_of_health_percent < t.degraded_soh:
        degraded_reasons.append(f"SOH below {t.degraded_soh}%")
    if battery.internal_resistance_mohm > t.degraded_resistance:
        degraded_reasons.append(f"Internal resistance above {t.degraded_resistance} mΩ")
    if battery.cell_voltage_imbalance_mv > t.degraded_imbalance:
        degraded_reasons.append(f"Cell imbalance above {t.degraded_imbalance} mV")
    if battery.cycle_count > t.degraded_cycle_count:
        degraded_reasons.append(f"Cycle count above {t.degraded_cycle_count}")

    if degraded_reasons:
        return BatteryClassification(
            battery_id=battery.battery_id,
            category=BatteryCategory.DEGRADED_USABLE,
            suitability_score=score,
            reasons=degraded_reasons,
        )

    return BatteryClassification(
        battery_id=battery.battery_id,
        category=BatteryCategory.SAFE_AVAILABLE,
        suitability_score=score,
        reasons=["All health parameters within safe operating limits"],
    )


def classify_fleet(
    batteries: list[Battery],
    thresholds: ThresholdConfig | None = None,
) -> dict[str, BatteryClassification]:
    return {b.battery_id: classify_battery(b, thresholds) for b in batteries}


def is_allocatable(classification: BatteryClassification) -> bool:
    return classification.category != BatteryCategory.UNSAFE_QUARANTINE
