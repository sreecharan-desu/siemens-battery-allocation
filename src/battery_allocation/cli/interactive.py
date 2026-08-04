"""Interactive CLI menu and file prompts."""

from __future__ import annotations

from pathlib import Path

from rich.prompt import Confirm, Prompt

from battery_allocation.cli.console import (
    console,
    print_banner,
    print_error,
    print_file_list,
    print_help,
    print_menu,
    print_metrics_table,
    print_note,
    print_ok,
    print_outputs,
    print_section,
    print_status_panel,
    run_with_spinner,
)
from battery_allocation.config.settings import get_settings
from battery_allocation.data.discovery import (
    copy_upload,
    discover_files,
    guess_battery_files,
    guess_vehicle_files,
    load_user_config,
    resolve_data_file,
    save_user_config,
)
from battery_allocation.data.loader import DataLoadError, validate_data_files
from battery_allocation.pipeline.runner import run_pipeline
from battery_allocation.utils.logging import setup_logging


def _short_path(path: Path) -> str:
    return path.name if len(str(path)) < 64 else f".../{path.name}"


def _pick_file(candidates: list[Path], label: str) -> Path | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        console.print(f"  {label}: {candidates[0].name}")
        return candidates[0]

    print_file_list(candidates, f"Select {label}")
    while True:
        choice = Prompt.ask("  number", default="1")
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            selected = candidates[int(choice) - 1]
            console.print(f"  {label}: {selected.name}")
            return selected
        print_error("invalid selection")


def _prompt_path(label: str) -> Path:
    while True:
        path_str = Prompt.ask(f"  {label}", default="").strip().strip('"').strip("'")
        if not path_str:
            print_error("path required")
            continue
        path = Path(path_str).expanduser().resolve()
        if not path.exists():
            print_error(f"file not found: {path}")
            continue
        if path.suffix.lower() not in {".csv", ".xlsx", ".xls"}:
            print_error("unsupported format (csv, xlsx, xls)")
            continue
        return path


def prompt_data_files(use_sample: bool = False) -> tuple[Path, Path]:
    settings = get_settings()
    root = settings.project_root

    if use_sample:
        battery_path = resolve_data_file(root, "battery", use_sample=True)
        vehicle_path = resolve_data_file(root, "vehicle", use_sample=True)
        console.print()
        console.print(f"  battery   {battery_path.name}")
        console.print(f"  vehicle   {vehicle_path.name}")
        return battery_path, vehicle_path

    print_section("Select data files")
    battery_candidates = guess_battery_files(root)
    vehicle_candidates = guess_vehicle_files(root)

    selected_battery = _pick_file(battery_candidates, "battery") if battery_candidates else None
    selected_vehicle = _pick_file(vehicle_candidates, "vehicle") if vehicle_candidates else None

    if selected_battery is None:
        selected_battery = _prompt_path("battery file")
    if selected_vehicle is None:
        selected_vehicle = _prompt_path("vehicle file")

    save_user_config(root, selected_battery, selected_vehicle)
    console.print()
    return selected_battery, selected_vehicle


def run_pipeline_interactive(use_sample: bool = False, skip_viz: bool = False) -> None:
    setup_logging("INFO", "text")
    battery, vehicle = prompt_data_files(use_sample=use_sample)
    settings = get_settings()
    output_dir = settings.resolved_output_dir()

    try:
        result = run_with_spinner(
            "running pipeline",
            lambda: run_pipeline(
                battery_csv=battery,
                vehicle_csv=vehicle,
                output_dir=output_dir,
                skip_visualizations=skip_viz,
            ),
        )
    except (DataLoadError, RuntimeError, FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        return

    print_metrics_table(result.proposed_metrics, result.baseline_metrics)
    print_ok("pipeline completed")
    print_outputs(result.output_paths)

    if Confirm.ask("  run again?", default=False):
        run_pipeline_interactive(use_sample=use_sample, skip_viz=skip_viz)


def upload_interactive() -> None:
    settings = get_settings()
    print_section("Upload")
    path = _prompt_path("file")
    try:
        dest = copy_upload(path, settings.project_root)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        return
    print_ok(f"uploaded {dest.name}")
    print_note("use 'run' to process this file")


def validate_interactive() -> None:
    setup_logging("WARNING", "text")
    print_section("Validate")
    battery, vehicle = prompt_data_files()
    try:
        info = run_with_spinner(
            "validating",
            lambda: validate_data_files(battery, vehicle),
        )
    except DataLoadError as exc:
        print_error(str(exc))
        return

    print_ok(f"{info['battery_count']} batteries, {info['vehicle_count']} requests")
    print_note(f"battery: {_short_path(Path(str(info['battery_file'])))}")
    print_note(f"vehicle: {_short_path(Path(str(info['vehicle_file'])))}")


def show_files() -> None:
    settings = get_settings()
    files = discover_files(settings.project_root)
    if not files:
        print_error("no data files found")
        print_note("upload a file or place CSV/Excel in data/")
        return
    print_file_list(files, "Data files")


def _show_active_config() -> None:
    settings = get_settings()
    cfg = load_user_config(settings.project_root)
    battery = cfg.get("battery_file")
    vehicle = cfg.get("vehicle_file")
    if battery or vehicle:
        print_status_panel(
            _short_path(Path(battery)) if battery else None,
            _short_path(Path(vehicle)) if vehicle else None,
        )


def interactive_menu() -> None:
    while True:
        console.print()
        print_banner()
        _show_active_config()
        print_menu()

        choice = Prompt.ask(">", default="2").strip().lower()

        if choice in {"1", "run"}:
            run_pipeline_interactive(use_sample=False)
        elif choice in {"2", "demo"}:
            run_pipeline_interactive(use_sample=True)
        elif choice in {"3", "upload"}:
            upload_interactive()
        elif choice in {"4", "files"}:
            show_files()
        elif choice in {"5", "validate"}:
            validate_interactive()
        elif choice in {"6", "serve"}:
            from battery_allocation.cli.main import serve_cmd

            serve_cmd(host=None, port=None, reload=False)
            break
        elif choice in {"7", "help"}:
            print_help()
        elif choice in {"q", "quit", "exit"}:
            break
        else:
            print_error(f"unknown command: {choice}")
