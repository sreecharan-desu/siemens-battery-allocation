"""REST API routes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from battery_allocation.core.classification import classify_fleet
from battery_allocation.core.twist import from_dict
from battery_allocation.data.loader import DataLoadError, load_batteries, load_vehicle_requests
from battery_allocation.pipeline.runner import run_pipeline

router = APIRouter()


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "battery-allocation"


class TwistRequest(BaseModel):
    name: str = "onsite_twist"
    exclude_degraded: bool = False
    min_soh_percent: float | None = None
    max_temperature_c: float | None = None
    priority_boost_critical: float = 0.0


class PipelineRequest(BaseModel):
    battery_csv: str | None = None
    vehicle_csv: str | None = None
    output_dir: str | None = None
    skip_visualizations: bool = False
    twist: TwistRequest | None = None


class PipelineResponse(BaseModel):
    success: bool
    proposed_metrics: dict[str, Any]
    baseline_metrics: dict[str, Any]
    output_paths: list[str]
    violations: list[str] = Field(default_factory=list)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.post("/pipeline/run", response_model=PipelineResponse)
def run_pipeline_endpoint(body: PipelineRequest) -> PipelineResponse:
    twist_ctx = from_dict(body.twist.model_dump()) if body.twist else None
    try:
        result = run_pipeline(
            battery_csv=Path(body.battery_csv) if body.battery_csv else None,
            vehicle_csv=Path(body.vehicle_csv) if body.vehicle_csv else None,
            output_dir=Path(body.output_dir) if body.output_dir else None,
            twist=twist_ctx,
            skip_visualizations=body.skip_visualizations,
        )
    except DataLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PipelineResponse(
        success=True,
        proposed_metrics=result.proposed_metrics,
        baseline_metrics=result.baseline_metrics,
        output_paths=result.output_paths,
        violations=result.violations_proposed + result.violations_baseline,
    )


@router.get("/classifications/summary")
def classifications_summary() -> dict[str, Any]:
    try:
        batteries = load_batteries()
    except DataLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    classifications = classify_fleet(batteries)
    summary: dict[str, int] = {}
    for cls in classifications.values():
        summary[cls.category.value] = summary.get(cls.category.value, 0) + 1

    return {
        "total_batteries": len(batteries),
        "by_category": summary,
    }


@router.get("/requests/summary")
def requests_summary() -> dict[str, Any]:
    try:
        requests = load_vehicle_requests()
    except DataLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    by_priority: dict[str, int] = {}
    for req in requests:
        by_priority[req.priority.value] = by_priority.get(req.priority.value, 0) + 1

    return {
        "total_requests": len(requests),
        "by_priority": by_priority,
    }
