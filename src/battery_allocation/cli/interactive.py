"""Interactive CLI menu and file prompts."""

from __future__ import annotations

from pathlib import Path

from rich.prompt import Confirm, Prompt

from battery_allocation.cli.console import (
    console,
    print_banner,
    print_divider,
    print_error,
    print_file_list,
    print_help,
    print_info,
    print_menu,
    print_metrics_table,
    print_outputs,
    print_status_panel,
    print_success,
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
    return path.name if len(str(path)) < 60 else f".../{path.name}"


def _pick_file(candidates: list[Path], label: str) -> Path | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        console.print(f"  [green]✓[/green] {label}: [cyan]{candidates[0].name}[/cyan]")
        return candidates[0]

    print_file_list(candidates, f"Select {label}")
    while True:
        choice = Prompt.ask(f"  Pick {label}", default="1")
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            selected = candidates[int(choice) - 1]
            console.print(f"  [green]✓[/green] Selected: [cyan]{selected.name}[/cyan]")
            return selected
        print_error("Invalid choice — enter a number from the list.")


def _prompt_path(label: str) -> Path:
    while True:
        path_str = Prompt.ask(f"  {label} path", default="").strip().strip('"').strip("'")
        if not path_str:
            print_error("Path cannot be empty.")
            continue
        path = Path(path_str).expanduser().resolve()
        if not path.exists():
            print_error(f"File not found: {path}")
            continue
        if path.suffix.lower() not in {".csv", ".xlsx", ".xls"}:
            print_error("Unsupported format — use CSV or Excel (.xlsx, .xls).")
            continue
        return path


def prompt_data_files(use_sample: bool = False) -> tuple[Path, Path]:
    settings = get_settings()
    root = settings.project_root

    if use_sample:
        battery_path = resolve_data_file(root, "battery", use_sample=True)
        vehicle_path = resolve_data_file(root, "vehicle", use_sample=True)
        console.print()
        print_info(f"Battery: [cyan]{battery_path.name}[/cyan]")
        print_info(f"Vehicle: [cyan]{vehicle_path.name}[/cyan]")
        return battery_path, vehicle_path

    print_divider("Select data files")
    battery_candidates = guess_battery_files(root)
    vehicle_candidates = guess_vehicle_files(root)

    selected_battery = _pick_file(battery_candidates, "battery fleet") if battery_candidates else None
    selected_vehicle = _pick_file(vehicle_candidates, "vehicle demand") if vehicle_candidates else None

    if selected_battery is None:
        selected_battery = _prompt_path("Battery fleet")
    if selected_vehicle is None:
        selected_vehicle = _prompt_path("Vehicle demand")

    save_user_config(root, selected_battery, selected_vehicle)
    console.print()
    return selected_battery, selected_vehicle


def run_pipeline_interactive(use_sample: bool = False, skip_viz: bool = False) -> None:
    setup_logging("INFO", "text")
    battery, vehicle = prompt_data_files(use_sample=use_sample)
    settings = get_settings()
    output_dir = settings.resolved_output_dir()

    console.print()
    try:
        result = run_with_spinner(
            "Running classification, allocation & reporting...",
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
    print_success("Pipeline completed successfully")
    print_outputs(result.output_paths)

    if Confirm.ask("  Run pipeline again?", default=False):
        run_pipeline_interactive(use_sample=use_sample, skip_viz=skip_viz)


def upload_interactive() -> None:
    settings = get_settings()
    print_divider("Upload data file")
    path = _prompt_path("File to upload")
    try:
        dest = copy_upload(path, settings.project_root)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        return
    print_success(f"Uploaded → [cyan]{dest.name}[/cyan]")
    print_info("Use option [bold]1[/bold] (Run pipeline) to use this file.")


def validate_interactive() -> None:
    setup_logging("WARNING", "text")
    print_divider("Validate data")
    battery, vehicle = prompt_data_files()
    try:
        info = run_with_spinner(
            "Validating data files...",
            lambda: validate_data_files(battery, vehicle),
        )
    except DataLoadError as exc:
        print_error(str(exc))
        return

    table_msg = (
        f"[bold]{info['battery_count']}[/bold] batteries  ·  "
        f"[bold]{info['vehicle_count']}[/bold] vehicle requests"
    )
    print_success(f"Data is valid — {table_msg}")
    print_info(f"Battery: [cyan]{_short_path(Path(str(info['battery_file'])))}[/cyan]")
    print_info(f"Vehicle: [cyan]{_short_path(Path(str(info['vehicle_file'])))}[/cyan]")


def show_files() -> None:
    settings = get_settings()
    files = discover_files(settings.project_root)
    if not files:
        print_error("No data files found.")
        print_info("Upload with option [bold]3[/bold] or place files in [cyan]data/[/cyan]")
        return
    print_file_list(files, "Available data files")


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


def _pause() -> None:
    console.print()
    Prompt.ask("  [dim]Press Enter to continue[/dim]", default="")


def interactive_menu() -> None:
    while True:
        console.clear()
        print_banner()
        _show_active_config()
        print_menu()

        choice = Prompt.ask("  Choose", default="2").strip().lower()

        if choice == "1":
            run_pipeline_interactive(use_sample=False)
            _pause()
        elif choice == "2":
            run_pipeline_interactive(use_sample=True)
            _pause()
        elif choice == "3":
            upload_interactive()
            _pause()
        elif choice == "4":
            show_files()
            _pause()
        elif choice == "5":
            validate_interactive()
            _pause()
        elif choice == "6":
            from battery_allocation.cli.main import serve_cmd

            print_divider("API Server")
            serve_cmd(host=None, port=None, reload=False)
            break
        elif choice == "7":
            print_help()
            _pause()
        elif choice in {"q", "quit", "exit"}:
            if Confirm.ask("  Quit battery-allocation?", default=True):
                console.print("\n  [dim]Goodbye! 👋[/dim]\n")
                break
        else:
            print_error(f"Unknown option: [bold]{choice}[/bold]")
            _pause()
