"""Battery-to-vehicle allocation algorithms."""

from __future__ import annotations

from battery_allocation.core.classification import classify_fleet, is_allocatable
from battery_allocation.core.models import (
    Allocation,
    Battery,
    BatteryCategory,
    BatteryClassification,
    VehicleRequest,
)


def _battery_meets_request(
    battery: Battery,
    classification: BatteryClassification,
    request: VehicleRequest,
) -> bool:
    return (
        is_allocatable(classification)
        and battery.state_of_charge_percent >= request.minimum_acceptable_soc_percent
        and battery.estimated_available_energy_kwh >= request.required_energy_kwh
    )


def _candidate_score(
    battery: Battery,
    classification: BatteryClassification,
    request: VehicleRequest,
) -> float:
    energy_margin = battery.estimated_available_energy_kwh - request.required_energy_kwh
    category_bonus = {
        BatteryCategory.SAFE_AVAILABLE: 15.0,
        BatteryCategory.DEGRADED_USABLE: 5.0,
        BatteryCategory.UNSAFE_QUARANTINE: -1000.0,
    }[classification.category]
    soc_balance = 10.0 - abs(battery.state_of_charge_percent - 75.0) * 0.05
    return classification.suitability_score + energy_margin * 20.0 + category_bonus + soc_balance


def allocate_highest_soc_first(
    batteries: list[Battery],
    requests: list[VehicleRequest],
    classifications: dict[str, BatteryClassification] | None = None,
) -> list[Allocation]:
    if classifications is None:
        classifications = classify_fleet(batteries)

    battery_map = {b.battery_id: b for b in batteries}
    allocated_batteries: set[str] = set()
    results: list[Allocation] = []

    for request in sorted(requests, key=lambda r: r.arrival_time):
        candidates: list[tuple[float, str]] = []
        for bid, cls in classifications.items():
            if bid in allocated_batteries:
                continue
            battery = battery_map[bid]
            if _battery_meets_request(battery, cls, request):
                candidates.append((battery.state_of_charge_percent, bid))

        if not candidates:
            results.append(
                Allocation(
                    request_id=request.request_id,
                    battery_id=None,
                    served=False,
                    reason="No eligible battery available",
                )
            )
            continue

        candidates.sort(key=lambda x: x[0], reverse=True)
        chosen_id = candidates[0][1]
        allocated_batteries.add(chosen_id)
        results.append(Allocation(request_id=request.request_id, battery_id=chosen_id, served=True))

    return results


def allocate_priority_suitability(
    batteries: list[Battery],
    requests: list[VehicleRequest],
    classifications: dict[str, BatteryClassification] | None = None,
) -> list[Allocation]:
    if classifications is None:
        classifications = classify_fleet(batteries)

    battery_map = {b.battery_id: b for b in batteries}
    allocated_batteries: set[str] = set()
    results: list[Allocation] = []

    for request in sorted(requests, key=lambda r: (-r.priority.weight, r.arrival_time)):
        candidates: list[tuple[float, str]] = []
        for bid, cls in classifications.items():
            if bid in allocated_batteries:
                continue
            battery = battery_map[bid]
            if _battery_meets_request(battery, cls, request):
                score = _candidate_score(battery, cls, request)
                candidates.append((score, bid))

        if not candidates:
            results.append(
                Allocation(
                    request_id=request.request_id,
                    battery_id=None,
                    served=False,
                    reason="No eligible battery available",
                )
            )
            continue

        candidates.sort(key=lambda x: x[0], reverse=True)
        chosen_id = candidates[0][1]
        allocated_batteries.add(chosen_id)
        results.append(Allocation(request_id=request.request_id, battery_id=chosen_id, served=True))

    result_map = {a.request_id: a for a in results}
    return [result_map[r.request_id] for r in sorted(requests, key=lambda x: x.arrival_time)]
