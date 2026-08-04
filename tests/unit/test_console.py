"""Tests for Rich console helpers."""

from __future__ import annotations

from pathlib import Path

from battery_allocation.cli import console as cli_console


def test_print_banner():
    cli_console.print_banner()


def test_print_menu():
    cli_console.print_menu()


def test_print_status_panel():
    cli_console.print_status_panel("battery.csv", "vehicle.csv")
    cli_console.print_status_panel()


def test_print_divider_and_messages():
    cli_console.print_divider("Section")
    cli_console.print_success("All good")
    cli_console.print_error("Something failed")
    cli_console.print_info("FYI")


def test_print_metrics_table():
    proposed = {
        "vehicles_served": 36,
        "vehicles_unserved": 14,
        "high_critical_served_pct": 73.08,
        "unsafe_allocations": 0,
        "avg_soh_allocated": 90.37,
        "avg_suitability_score": 84.54,
    }
    baseline = {
        "vehicles_served": 36,
        "vehicles_unserved": 14,
        "high_critical_served_pct": 69.23,
        "unsafe_allocations": 0,
        "avg_soh_allocated": 80.49,
        "avg_suitability_score": 76.80,
    }
    cli_console.print_metrics_table(proposed, baseline)


def test_print_file_list(tmp_path: Path):
    f = tmp_path / "battery_fleet.csv"
    f.write_text("a\n1\n", encoding="utf-8")
    cli_console.print_file_list([f], "Files")


def test_print_outputs():
    cli_console.print_outputs(["/tmp/a.csv", "/tmp/b.json"])


def test_print_help():
    cli_console.print_help()


def test_run_with_spinner():
    result = cli_console.run_with_spinner("working", lambda: "done")
    assert result == "done"


def test_format_metric_styles():
    label, proposed, baseline = cli_console._format_metric("Vehicles served", 40, 36)
    assert label == "Vehicles served"
    assert "40" in proposed
    assert baseline == "36"

    _, proposed2, _ = cli_console._format_metric("Unsafe allocations", 1, 0)
    assert "1" in proposed2

    _, proposed3, _ = cli_console._format_metric("Vehicles unserved", 5, 10)
    assert "5" in proposed3


def test_interactive_show_files(project_root: Path):
    from battery_allocation.cli.interactive import show_files

    show_files()


def test_prompt_data_files_sample(project_root: Path):
    from battery_allocation.cli.interactive import prompt_data_files

    battery, vehicle = prompt_data_files(use_sample=True)
    assert battery.exists()
    assert vehicle.exists()
