"""Command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from battery_allocation.config.settings import get_settings
from battery_allocation.core.twist import from_dict
from battery_allocation.data.loader import DataLoadError
from battery_allocation.pipeline.runner import run_pipeline
from battery_allocation.utils.logging import setup_logging

app = typer.Typer(
    name="battery-allocation",
    help="Battery health assessment and dynamic allocation for light EV stations.",
    no_args_is_help=True,
)


@app.command("run")
def run_cmd(
    battery_csv: Annotated[Path | None, typer.Option("--battery-csv", help="Battery fleet CSV")] = None,
    vehicle_csv: Annotated[Path | None, typer.Option("--vehicle-csv", help="Vehicle demand CSV")] = None,
    output_dir: Annotated[Path | None, typer.Option("--output-dir", help="Output directory")] = None,
    twist_json: Annotated[str | None, typer.Option("--twist-json", help="JSON twist parameters")] = None,
    skip_viz: Annotated[bool, typer.Option("--skip-viz", help="Skip chart generation")] = False,
    log_level: Annotated[str | None, typer.Option("--log-level")] = None,
) -> None:
    """Run the full classification, allocation, and reporting pipeline."""
    settings = get_settings()
    log_fmt = "json" if settings.log_format == "json" else "text"
    setup_logging(log_level or settings.log_level, log_fmt)

    twist = from_dict(json.loads(twist_json)) if twist_json else None
    try:
        result = run_pipeline(
            battery_csv=battery_csv,
            vehicle_csv=vehicle_csv,
            output_dir=output_dir,
            twist=twist,
            skip_visualizations=skip_viz,
        )
    except (DataLoadError, RuntimeError) as exc:
        typer.secho(f"Pipeline failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho("Pipeline completed successfully.", fg=typer.colors.GREEN)
    typer.echo(
        json.dumps(
            {"proposed_metrics": result.proposed_metrics, "baseline_metrics": result.baseline_metrics},
            indent=2,
        )
    )
    for path in result.output_paths:
        typer.echo(f"  -> {path}")


@app.command("serve")
def serve_cmd(
    host: Annotated[str | None, typer.Option("--host")] = None,
    port: Annotated[int | None, typer.Option("--port")] = None,
    reload: Annotated[bool, typer.Option("--reload", help="Enable auto-reload")] = False,
) -> None:
    """Start the REST API server."""
    settings = get_settings()
    setup_logging(settings.log_level, "text")
    uvicorn.run(
        "battery_allocation.api.app:create_app",
        factory=True,
        host=host or settings.api_host,
        port=port or settings.api_port,
        reload=reload,
    )


def run_cli() -> None:
    app()
