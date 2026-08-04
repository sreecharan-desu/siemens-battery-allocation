"""CLI output — minimal, tool-style formatting."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TypeVar

from rich.console import Console
from rich.status import Status
from rich.table import Table

from battery_allocation import __version__

console = Console(highlight=False, soft_wrap=True)
T = TypeVar("T")

MENU_ITEMS: list[tuple[str, str, str]] = [
    ("1", "run", "Run pipeline with your data files"),
    ("2", "demo", "Run with bundled sample data"),
    ("3", "upload", "Upload a CSV or Excel file"),
    ("4", "files", "List available data files"),
    ("5", "validate", "Validate data without running"),
    ("6", "serve", "Start API server"),
    ("7", "help", "Show command reference"),
    ("q", "quit", "Exit"),
]


def print_banner() -> None:
    console.print(f"battery-allocation {__version__}")
    console.print("[dim]Battery health assessment and dynamic allocation[/dim]")
    console.print()


def print_status_panel(battery: str | None = None, vehicle: str | None = None) -> None:
    console.print("[dim]Context[/dim]")
    console.print(f"  battery   {battery or '-'}")
    console.print(f"  vehicle   {vehicle or '-'}")
    console.print()


def print_menu() -> None:
    console.print("[dim]Commands[/dim]")
    for key, cmd, desc in MENU_ITEMS:
        console.print(f"  {key:<3} {cmd:<10} {desc}")
    console.print()


def print_section(title: str) -> None:
    console.print()
    console.print(f"[dim]{title}[/dim]")


def print_ok(message: str) -> None:
    console.print(f"ok  {message}")


def print_error(message: str) -> None:
    console.print(f"error  {message}")


def print_note(message: str) -> None:
    console.print(f"[dim]{message}[/dim]")


def _format_metric(label: str, proposed: object, baseline: object) -> tuple[str, str, str]:
    p_str = str(proposed) if proposed is not None else "-"
    b_str = str(baseline) if baseline is not None else "-"
    return label, p_str, b_str


def print_metrics_table(proposed: dict[str, object], baseline: dict[str, object]) -> None:
    table = Table(show_header=True, header_style="dim", box=None, padding=(0, 2))
    table.add_column("metric", min_width=24)
    table.add_column("proposed", justify="right")
    table.add_column("baseline", justify="right")

    rows = [
        ("vehicles served", "vehicles_served"),
        ("vehicles unserved", "vehicles_unserved"),
        ("high/critical served %", "high_critical_served_pct"),
        ("unsafe allocations", "unsafe_allocations"),
        ("avg SoH allocated", "avg_soh_allocated"),
        ("avg suitability score", "avg_suitability_score"),
    ]
    for label, key in rows:
        p_val = proposed.get(key)
        b_val = baseline.get(key)
        lbl, p_fmt, b_fmt = _format_metric(label, p_val, b_val)
        table.add_row(lbl, p_fmt, b_fmt)

    console.print()
    console.print("[dim]Results[/dim]")
    console.print(table)
    console.print()


def print_file_list(files: list[Path], title: str) -> None:
    table = Table(show_header=True, header_style="dim", box=None, padding=(0, 1))
    table.add_column("#", justify="right", width=3)
    table.add_column("file")
    table.add_column("type", width=6)
    table.add_column("size", justify="right", width=10)

    for i, f in enumerate(files, 1):
        size_kb = f.stat().st_size / 1024
        ext = f.suffix.lower().lstrip(".") or "-"
        table.add_row(str(i), f.name, ext, f"{size_kb:.1f} KB")

    console.print()
    console.print(f"[dim]{title}[/dim]")
    console.print(table)
    console.print()


def print_outputs(paths: list[str]) -> None:
    console.print("[dim]Outputs[/dim]")
    for path in paths:
        console.print(f"  {path}")
    console.print()


def print_help() -> None:
    console.print()
    console.print("[dim]Commands[/dim]")
    lines = [
        ("battery-allocation", "interactive menu"),
        ("battery-allocation run", "run pipeline (auto-discover data)"),
        ("battery-allocation run --sample", "run with bundled sample data"),
        ("battery-allocation run -b FILE -v FILE", "run with explicit files"),
        ("battery-allocation upload FILE", "upload CSV or Excel"),
        ("battery-allocation files", "list data files"),
        ("battery-allocation validate", "validate data files"),
        ("battery-allocation serve", "start REST API"),
        ("battery-allocation version", "print version"),
    ]
    for cmd, desc in lines:
        console.print(f"  {cmd:<40} {desc}")
    console.print()


@contextmanager
def spinner(message: str) -> Iterator[None]:
    with Status(f"  {message}", console=console, spinner="line") as status:
        yield
        status.stop()


def run_with_spinner(message: str, func: Callable[[], T]) -> T:
    with spinner(message):
        return func()


# Backward-compatible aliases used elsewhere
print_divider = print_section
print_success = print_ok
print_info = print_note
