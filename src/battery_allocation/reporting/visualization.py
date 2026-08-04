"""Generate reports and visualizations."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from battery_allocation.core.models import (
    Allocation,
    BatteryCategory,
    BatteryClassification,
    VehicleRequest,
)
from battery_allocation.reporting.metrics import AllocationMetrics


def _ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def plot_battery_classification(
    classifications: dict[str, BatteryClassification],
    output_dir: Path,
) -> Path:
    _ensure_output_dir(output_dir)
    categories = [c.category.value for c in classifications.values()]
    counts = pd.Series(categories).value_counts()

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = {
        BatteryCategory.SAFE_AVAILABLE.value: "#2ecc71",
        BatteryCategory.DEGRADED_USABLE.value: "#f39c12",
        BatteryCategory.UNSAFE_QUARANTINE.value: "#e74c3c",
    }
    bar_colors = [colors.get(cat, "#95a5a6") for cat in counts.index]
    counts.plot(kind="bar", ax=ax, color=bar_colors, edgecolor="black")
    ax.set_title("Battery Classification Distribution")
    ax.set_xlabel("Category")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=15)
    plt.tight_layout()
    path = output_dir / "01_battery_classification.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_suitability_distribution(
    classifications: dict[str, BatteryClassification],
    output_dir: Path,
) -> Path:
    _ensure_output_dir(output_dir)
    scores = [c.suitability_score for c in classifications.values()]
    categories = [c.category.value for c in classifications.values()]

    fig, ax = plt.subplots(figsize=(9, 5))
    color_map = {
        BatteryCategory.SAFE_AVAILABLE.value: "#2ecc71",
        BatteryCategory.DEGRADED_USABLE.value: "#f39c12",
        BatteryCategory.UNSAFE_QUARANTINE.value: "#e74c3c",
    }
    for cat in color_map:
        cat_scores = [s for s, c in zip(scores, categories, strict=True) if c == cat]
        if cat_scores:
            ax.hist(cat_scores, bins=15, alpha=0.7, label=cat, color=color_map[cat])

    ax.set_title("Battery Suitability Score Distribution by Category")
    ax.set_xlabel("Suitability Score (0–100)")
    ax.set_ylabel("Frequency")
    ax.legend()
    plt.tight_layout()
    path = output_dir / "02_suitability_score_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_quarantine_batteries(
    classifications: dict[str, BatteryClassification],
    output_dir: Path,
) -> Path:
    _ensure_output_dir(output_dir)
    unsafe = [
        c for c in classifications.values()
        if c.category == BatteryCategory.UNSAFE_QUARANTINE
    ]
    ids = [c.battery_id for c in unsafe]
    scores = [c.suitability_score for c in unsafe]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(ids, scores, color="#e74c3c", edgecolor="black")
    ax.set_title("Unsafe / Quarantine Batteries Identified")
    ax.set_xlabel("Battery ID")
    ax.set_ylabel("Suitability Score")
    ax.tick_params(axis="x", rotation=90)
    plt.tight_layout()
    path = output_dir / "05_quarantine_batteries.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_allocation_by_priority(
    allocations: list[Allocation],
    requests: list[VehicleRequest],
    method_name: str,
    output_dir: Path,
) -> Path:
    _ensure_output_dir(output_dir)
    request_map = {r.request_id: r for r in requests}
    rows = [
        {
            "priority": request_map[a.request_id].priority.value,
            "served": "Served" if a.served else "Unserved",
        }
        for a in allocations
    ]
    df = pd.DataFrame(rows)
    pivot = df.groupby(["priority", "served"]).size().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(8, 5))
    pivot.plot(kind="bar", ax=ax, color=["#e74c3c", "#2ecc71"], edgecolor="black")
    ax.set_title(f"Allocation Results by Priority ({method_name})")
    ax.set_xlabel("Priority")
    ax.set_ylabel("Number of Requests")
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="Status")
    plt.tight_layout()
    path = output_dir / f"03_allocation_by_priority_{method_name.lower().replace(' ', '_')}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_method_comparison(
    proposed_metrics: AllocationMetrics,
    baseline_metrics: AllocationMetrics,
    output_dir: Path,
) -> Path:
    _ensure_output_dir(output_dir)
    metric_keys = [
        "vehicles_served",
        "high_critical_served_pct",
        "avg_soh_allocated",
        "avg_suitability_score",
    ]
    labels = [
        "Vehicles Served",
        "High/Critical Served (%)",
        "Avg SoH Allocated",
        "Avg Suitability Score",
    ]

    proposed_vals = [getattr(proposed_metrics, m) for m in metric_keys]
    baseline_vals = [getattr(baseline_metrics, m) for m in metric_keys]

    x = range(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([i - width / 2 for i in x], baseline_vals, width, label="Highest-SoC-First", color="#3498db")
    ax.bar([i + width / 2 for i in x], proposed_vals, width, label="Priority-Suitability", color="#9b59b6")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_title("Proposed Method vs Highest-SoC-First Baseline")
    ax.legend()
    plt.tight_layout()
    path = output_dir / "04_method_comparison.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def generate_all_visualizations(
    classifications: dict[str, BatteryClassification],
    proposed_allocations: list[Allocation],
    baseline_allocations: list[Allocation],
    requests: list[VehicleRequest],
    proposed_metrics: AllocationMetrics,
    baseline_metrics: AllocationMetrics,
    output_dir: Path,
    include_quarantine: bool = True,
) -> list[Path]:
    paths = [
        plot_battery_classification(classifications, output_dir),
        plot_suitability_distribution(classifications, output_dir),
        plot_allocation_by_priority(proposed_allocations, requests, "Proposed", output_dir),
        plot_method_comparison(proposed_metrics, baseline_metrics, output_dir),
    ]
    if include_quarantine:
        paths.append(plot_quarantine_batteries(classifications, output_dir))
    return paths
