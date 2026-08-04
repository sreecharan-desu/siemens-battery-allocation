"""End-to-end pipeline orchestration."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from battery_allocation.config.settings import get_pipeline_config, get_settings
from battery_allocation.core.allocation import (
    allocate_highest_soc_first,
    allocate_priority_suitability,
)
from battery_allocation.core.classification import classify_fleet
from battery_allocation.core.models import PipelineResult
from battery_allocation.core.twist import TwistContext, apply_twist_filters
from battery_allocation.data.loader import load_batteries, load_vehicle_requests
from battery_allocation.pipeline.exporters import (
    export_allocations,
    export_classifications,
    export_metrics_report,
    export_quarantine_report,
)
from battery_allocation.reporting.metrics import compute_metrics, verify_allocations
from battery_allocation.reporting.visualization import generate_all_visualizations

logger = logging.getLogger(__name__)


def _configure_matplotlib() -> None:
    settings = get_settings()
    mpl_dir = settings.resolved_mpl_config_dir()
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))


def run_pipeline(
    battery_csv: Path | None = None,
    vehicle_csv: Path | None = None,
    output_dir: Path | None = None,
    twist: TwistContext | None = None,
    skip_visualizations: bool = False,
) -> PipelineResult:
    _configure_matplotlib()
    settings = get_settings()
    pipeline_cfg = get_pipeline_config().get("pipeline", {})
    reporting_cfg = get_pipeline_config().get("reporting", {})

    out = output_dir or settings.resolved_output_dir()
    out.mkdir(parents=True, exist_ok=True)

    batteries = load_batteries(battery_csv)
    requests = load_vehicle_requests(vehicle_csv)

    if twist:
        logger.info("Applying twist: %s", twist.name)
        batteries, requests = apply_twist_filters(twist, batteries, requests)

    classifications = classify_fleet(batteries)
    output_paths: list[str] = []

    class_path = export_classifications(classifications, out)
    output_paths.append(str(class_path))
    logger.info("Exported classifications to %s", class_path)

    if reporting_cfg.get("export_quarantine_report", True):
        quar_path = export_quarantine_report(classifications, out)
        output_paths.append(str(quar_path))

    proposed = allocate_priority_suitability(batteries, requests, classifications)
    baseline = allocate_highest_soc_first(batteries, requests, classifications)

    proposed_path = export_allocations(proposed, "proposed", out)
    baseline_path = export_allocations(baseline, "baseline_highest_soc", out)
    output_paths.extend([str(proposed_path), str(baseline_path)])

    violations_proposed: list[str] = []
    violations_baseline: list[str] = []
    if pipeline_cfg.get("verify_constraints", True):
        violations_proposed = verify_allocations(proposed, batteries, requests, classifications)
        violations_baseline = verify_allocations(baseline, batteries, requests, classifications)
        if violations_proposed or violations_baseline:
            logger.error("Constraint violations detected")
            for v in violations_proposed + violations_baseline:
                logger.error("  %s", v)
            raise RuntimeError("Allocation constraint verification failed")

    proposed_metrics = compute_metrics(
        "Priority-Suitability", proposed, batteries, requests, classifications
    )
    baseline_metrics = compute_metrics(
        "Highest-SoC-First", baseline, batteries, requests, classifications
    )
    metrics_path = export_metrics_report(proposed_metrics, baseline_metrics, out)
    output_paths.append(str(metrics_path))

    generate_viz = not skip_visualizations and pipeline_cfg.get("generate_visualizations", True)
    if generate_viz:
        viz_paths = generate_all_visualizations(
            classifications,
            proposed,
            baseline,
            requests,
            proposed_metrics,
            baseline_metrics,
            out,
            include_quarantine=reporting_cfg.get("export_quarantine_report", True),
        )
        output_paths.extend(str(p) for p in viz_paths)

    logger.info(
        "Pipeline complete: served=%d (proposed), served=%d (baseline)",
        proposed_metrics.vehicles_served,
        baseline_metrics.vehicles_served,
    )

    return PipelineResult(
        classifications=classifications,
        proposed_allocations=proposed,
        baseline_allocations=baseline,
        proposed_metrics=proposed_metrics.to_dict(),
        baseline_metrics=baseline_metrics.to_dict(),
        violations_proposed=violations_proposed,
        violations_baseline=violations_baseline,
        output_paths=output_paths,
    )
