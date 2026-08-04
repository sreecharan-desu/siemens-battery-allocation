"""Export pipeline results to CSV, JSON, and reports."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from battery_allocation.core.models import Allocation, BatteryCategory, BatteryClassification
from battery_allocation.reporting.metrics import AllocationMetrics


def export_classifications(
    classifications: dict[str, BatteryClassification],
    output_dir: Path,
) -> Path:
    rows = [
        {
            "battery_id": bid,
            "category": cls.category.value,
            "suitability_score": cls.suitability_score,
            "reasons": "; ".join(cls.reasons),
        }
        for bid, cls in classifications.items()
    ]
    path = output_dir / "battery_classifications.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def export_quarantine_report(
    classifications: dict[str, BatteryClassification],
    output_dir: Path,
) -> Path:
    rows = [
        {
            "battery_id": cls.battery_id,
            "category": cls.category.value,
            "suitability_score": cls.suitability_score,
            "reasons": "; ".join(cls.reasons),
        }
        for cls in classifications.values()
        if cls.category == BatteryCategory.UNSAFE_QUARANTINE
    ]
    path = output_dir / "quarantine_report.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def export_allocations(
    allocations: list[Allocation],
    method_name: str,
    output_dir: Path,
) -> Path:
    rows = [
        {
            "request_id": a.request_id,
            "battery_id": a.battery_id or "",
            "served": a.served,
            "reason": a.reason,
        }
        for a in allocations
    ]
    safe_name = method_name.lower().replace(" ", "_").replace("-", "_")
    path = output_dir / f"allocations_{safe_name}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def export_metrics_report(
    proposed: AllocationMetrics,
    baseline: AllocationMetrics,
    output_dir: Path,
) -> Path:
    report = {"proposed": proposed.to_dict(), "baseline": baseline.to_dict()}
    path = output_dir / "metrics_report.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return path
