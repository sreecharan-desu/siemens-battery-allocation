"""Onsite twist handler — plug in event-day constraint changes without rewriting core logic."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from battery_allocation.core.models import Battery, VehicleRequest


@dataclass
class TwistContext:
    """Runtime twist parameters applied during allocation."""

    name: str = "none"
    exclude_degraded: bool = False
    min_soh_percent: float | None = None
    max_temperature_c: float | None = None
    priority_boost_critical: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


TwistHandler = Callable[[TwistContext, list[Battery], list[VehicleRequest]], TwistContext]


def apply_twist_filters(
    twist: TwistContext,
    batteries: list[Battery],
    requests: list[VehicleRequest],
) -> tuple[list[Battery], list[VehicleRequest]]:
    """Filter inputs according to twist rules before allocation."""
    filtered_batteries = batteries
    if twist.min_soh_percent is not None:
        filtered_batteries = [
            b for b in filtered_batteries if b.state_of_health_percent >= twist.min_soh_percent
        ]
    if twist.max_temperature_c is not None:
        filtered_batteries = [
            b for b in filtered_batteries if b.temperature_c <= twist.max_temperature_c
        ]
    return filtered_batteries, list(requests)


def from_dict(data: dict[str, object]) -> TwistContext:
    min_soh = data.get("min_soh_percent")
    max_temp = data.get("max_temperature_c")
    boost = data.get("priority_boost_critical", 0.0)
    return TwistContext(
        name=str(data.get("name", "custom")),
        exclude_degraded=bool(data.get("exclude_degraded", False)),
        min_soh_percent=float(min_soh) if isinstance(min_soh, (int, float, str)) else None,
        max_temperature_c=float(max_temp) if isinstance(max_temp, (int, float, str)) else None,
        priority_boost_critical=float(boost) if isinstance(boost, (int, float, str)) else 0.0,
        metadata={
            k: v
            for k, v in data.items()
            if k
            not in {
                "name",
                "exclude_degraded",
                "min_soh_percent",
                "max_temperature_c",
                "priority_boost_critical",
            }
        },
    )
