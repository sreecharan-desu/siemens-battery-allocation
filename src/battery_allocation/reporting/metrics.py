"""Quantitative metrics and constraint verification."""

from __future__ import annotations

from dataclasses import dataclass

from battery_allocation.core.classification import classify_fleet, is_allocatable
from battery_allocation.core.models import (
    Allocation,
    Battery,
    BatteryClassification,
    VehiclePriority,
    VehicleRequest,
)


@dataclass
class AllocationMetrics:
    method_name: str
    vehicles_served: int
    vehicles_unserved: int
    high_critical_served_pct: float
    unsafe_allocations: int
    avg_soh_allocated: float
    avg_suitability_score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method_name,
            "vehicles_served": self.vehicles_served,
            "vehicles_unserved": self.vehicles_unserved,
            "high_critical_served_pct": round(self.high_critical_served_pct, 2),
            "unsafe_allocations": self.unsafe_allocations,
            "avg_soh_allocated": round(self.avg_soh_allocated, 2),
            "avg_suitability_score": round(self.avg_suitability_score, 2),
        }


def compute_metrics(
    method_name: str,
    allocations: list[Allocation],
    batteries: list[Battery],
    requests: list[VehicleRequest],
    classifications: dict[str, BatteryClassification],
) -> AllocationMetrics:
    battery_map = {b.battery_id: b for b in batteries}
    request_map = {r.request_id: r for r in requests}

    served = [a for a in allocations if a.served and a.battery_id]
    unserved = [a for a in allocations if not a.served]

    high_critical_requests = [
        r for r in requests if r.priority in (VehiclePriority.HIGH, VehiclePriority.CRITICAL)
    ]
    high_critical_served = sum(
        1
        for a in allocations
        if a.served
        and request_map[a.request_id].priority in (VehiclePriority.HIGH, VehiclePriority.CRITICAL)
    )
    high_critical_pct = (
        (high_critical_served / len(high_critical_requests) * 100.0)
        if high_critical_requests
        else 0.0
    )

    unsafe_count = 0
    soh_values: list[float] = []
    suitability_values: list[float] = []

    for alloc in served:
        if alloc.battery_id is None:
            continue
        cls = classifications[alloc.battery_id]
        battery = battery_map[alloc.battery_id]
        if not is_allocatable(cls):
            unsafe_count += 1
        soh_values.append(battery.state_of_health_percent)
        suitability_values.append(cls.suitability_score)

    return AllocationMetrics(
        method_name=method_name,
        vehicles_served=len(served),
        vehicles_unserved=len(unserved),
        high_critical_served_pct=high_critical_pct,
        unsafe_allocations=unsafe_count,
        avg_soh_allocated=sum(soh_values) / len(soh_values) if soh_values else 0.0,
        avg_suitability_score=sum(suitability_values) / len(suitability_values)
        if suitability_values
        else 0.0,
    )


def verify_allocations(
    allocations: list[Allocation],
    batteries: list[Battery],
    requests: list[VehicleRequest],
    classifications: dict[str, BatteryClassification] | None = None,
) -> list[str]:
    if classifications is None:
        classifications = classify_fleet(batteries)

    violations: list[str] = []
    battery_map = {b.battery_id: b for b in batteries}
    request_map = {r.request_id: r for r in requests}
    used_batteries: dict[str, str] = {}

    for alloc in allocations:
        if alloc.served and alloc.battery_id:
            if alloc.battery_id in used_batteries:
                violations.append(
                    f"Battery {alloc.battery_id} assigned to multiple vehicles "
                    f"({used_batteries[alloc.battery_id]} and {alloc.request_id})"
                )
            used_batteries[alloc.battery_id] = alloc.request_id

            cls = classifications[alloc.battery_id]
            if not is_allocatable(cls):
                violations.append(
                    f"Unsafe battery {alloc.battery_id} allocated to {alloc.request_id}"
                )

            battery = battery_map[alloc.battery_id]
            request = request_map[alloc.request_id]
            if battery.state_of_charge_percent < request.minimum_acceptable_soc_percent:
                violations.append(
                    f"Battery {alloc.battery_id} SOC below minimum for {alloc.request_id}"
                )

    if sum(1 for a in allocations if a.served) > len(requests):
        violations.append("More allocations than vehicle requests")

    return violations
