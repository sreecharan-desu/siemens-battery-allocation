"""Command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from battery_allocation import __version__
from battery_allocation.cli.console import (
    console,
    print_error,
    print_metrics_table,
    print_note,
    print_ok,
    print_outputs,
)
from battery_allocation.cli.interactive import interactive_menu
from battery_allocation.config.settings import get_settings
from battery_allocation.core.twist import from_dict
from battery_allocation.data.discovery import (
    copy_upload,
    resolve_data_file,
    save_user_config,
)
from battery_allocation.data.loader import DataLoadError, validate_data_files
from battery_allocation.pipeline.runner import run_pipeline
from battery_allocation.utils.logging import setup_logging

app = typer.Typer(
    name="battery-allocation",
    help="Battery health assessment and dynamic allocation for light EV stations.",
    no_args_is_help=False,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Launch interactive menu when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        interactive_menu()


@app.command("run")
def run_cmd(
    battery: Annotated[
        Path | None,
        typer.Option("--battery", "-b", help="Battery fleet file (CSV or Excel)"),
    ] = None,
    vehicle: Annotated[
        Path | None,
        typer.Option("--vehicle", "-v", help="Vehicle demand file (CSV or Excel)"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output directory"),
    ] = None,
    sample: Annotated[
        bool,
        typer.Option("--sample", help="Use bundled sample competition datasets"),
    ] = False,
    twist_json: Annotated[str | None, typer.Option("--twist-json", help="JSON twist parameters")] = None,
    skip_viz: Annotated[bool, typer.Option("--skip-viz", help="Skip chart generation")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Print metrics as JSON")] = False,
    log_level: Annotated[str | None, typer.Option("--log-level")] = None,
) -> None:
    """Run classification, allocation, and reporting pipeline."""
    settings = get_settings()
    log_fmt = "json" if settings.log_format == "json" else "text"
    setup_logging(log_level or settings.log_level, log_fmt)

    try:
        battery_path = resolve_data_file(settings.project_root, "battery", battery, use_sample=sample)
        vehicle_path = resolve_data_file(settings.project_root, "vehicle", vehicle, use_sample=sample)
        save_user_config(settings.project_root, battery_path, vehicle_path)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        raise typer.Exit(code=1) from exc

    twist = from_dict(json.loads(twist_json)) if twist_json else None
    try:
        result = run_pipeline(
            battery_csv=battery_path,
            vehicle_csv=vehicle_path,
            output_dir=output,
            twist=twist,
            skip_visualizations=skip_viz,
        )
    except (DataLoadError, RuntimeError) as exc:
        print_error(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(
            json.dumps(
                {"proposed_metrics": result.proposed_metrics, "baseline_metrics": result.baseline_metrics},
                indent=2,
            )
        )
    else:
        print_ok("pipeline completed")
        print_metrics_table(result.proposed_metrics, result.baseline_metrics)
        print_outputs(result.output_paths)


@app.command("upload")
def upload_cmd(
    file: Annotated[
        Path,
        typer.Argument(help="CSV or Excel file to copy into data/uploads/"),
    ],
) -> None:
    """Upload a CSV or Excel data file for use in the pipeline."""
    settings = get_settings()
    try:
        dest = copy_upload(file, settings.project_root)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        raise typer.Exit(code=1) from exc
    print_ok(f"uploaded {dest.name}")
    print_note("run: battery-allocation run")


@app.command("files")
def files_cmd() -> None:
    """List all discoverable CSV/Excel data files."""
    from battery_allocation.cli.interactive import show_files

    show_files()


@app.command("validate")
def validate_cmd(
    battery: Annotated[Path | None, typer.Option("--battery", "-b")] = None,
    vehicle: Annotated[Path | None, typer.Option("--vehicle", "-v")] = None,
    sample: Annotated[bool, typer.Option("--sample", help="Validate sample datasets")] = False,
) -> None:
    """Validate data files without running the full pipeline."""
    settings = get_settings()
    try:
        battery_path = resolve_data_file(settings.project_root, "battery", battery, use_sample=sample)
        vehicle_path = resolve_data_file(settings.project_root, "vehicle", vehicle, use_sample=sample)
        info = validate_data_files(battery_path, vehicle_path)
    except (DataLoadError, FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        raise typer.Exit(code=1) from exc
    console.print(
        f"ok  {info['battery_count']} batteries, {info['vehicle_count']} requests\n"
        f"  battery  {info['battery_file']}\n"
        f"  vehicle  {info['vehicle_file']}"
    )


@app.command("serve")
def serve_cmd(
    host: Annotated[str | None, typer.Option("--host")] = None,
    port: Annotated[int | None, typer.Option("--port")] = None,
    reload: Annotated[bool, typer.Option("--reload", help="Enable auto-reload")] = False,
) -> None:
    """Start the REST API server."""
    settings = get_settings()
    setup_logging(settings.log_level, "text")
    console.print(f"listening on http://{host or settings.api_host}:{port or settings.api_port}/docs")
    uvicorn.run(
        "battery_allocation.api.app:create_app",
        factory=True,
        host=host or settings.api_host,
        port=port or settings.api_port,
        reload=reload,
    )


@app.command("version")
def version_cmd() -> None:
    """Show installed version."""
    console.print(f"battery-allocation {__version__}")


def run_cli() -> None:
    app()


if __name__ == "__main__":
    run_cli()
