"""Rich console helpers for CLI output."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TypeVar

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.status import Status
from rich.table import Table
from rich.text import Text

from battery_allocation import __version__

console = Console()
T = TypeVar("T")

MENU_ITEMS: list[tuple[str, str, str]] = [
    ("1", "Run pipeline", "Use your CSV or Excel files"),
    ("2", "Quick demo", "Bundled sample competition data"),
    ("3", "Upload file", "Add CSV/Excel to data/uploads/"),
    ("4", "Browse files", "See all discoverable data files"),
    ("5", "Validate data", "Check files without running pipeline"),
    ("6", "API server", "Start REST API + docs"),
    ("7", "Help", "Command reference"),
    ("q", "Quit", "Exit the CLI"),
]


def print_banner() -> None:
    title = Text()
    title.append("⚡ ", style="bold yellow")
    title.append("Battery Allocation", style="bold cyan")
    title.append(f"  v{__version__}", style="dim")

    subtitle = Text("Classify  ·  Score  ·  Allocate  ·  Report", style="dim italic", justify="center")

    console.print()
    console.print(
        Panel(
            Align.center(Group(title, "", subtitle)),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 4),
        )
    )
    console.print()


def print_status_panel(battery: str | None = None, vehicle: str | None = None) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()

    table.add_row("Battery", battery or "[dim]not set[/dim]")
    table.add_row("Vehicle", vehicle or "[dim]not set[/dim]")

    console.print(Panel(table, title="[bold]Active data[/bold]", border_style="blue", box=box.ROUNDED))
    console.print()


def print_menu() -> None:
    table = Table(
        title="[bold]What would you like to do?[/bold]",
        show_header=True,
        header_style="bold magenta",
        box=box.SIMPLE_HEAD,
        padding=(0, 1),
        expand=False,
    )
    table.add_column("Key", style="bold cyan", width=4, justify="center")
    table.add_column("Action", style="bold white")
    table.add_column("Description", style="dim")

    for key, action, desc in MENU_ITEMS:
        table.add_row(key, action, desc)

    console.print(table)
    console.print()


def print_divider(title: str = "") -> None:
    console.print(Rule(title, style="dim"))


def print_success(message: str) -> None:
    console.print(Panel(f"[bold green]✓[/bold green]  {message}", border_style="green", box=box.ROUNDED))


def print_error(message: str) -> None:
    console.print(Panel(f"[bold red]✗[/bold red]  {message}", border_style="red", box=box.ROUNDED))


def print_info(message: str) -> None:
    console.print(f"[blue]ℹ[/blue]  {message}")


def _format_metric(label: str, proposed: object, baseline: object) -> tuple[str, str, str]:
    p_str = str(proposed) if proposed is not None else "—"
    b_str = str(baseline) if baseline is not None else "—"

    style_p = ""
    if isinstance(proposed, (int, float)) and isinstance(baseline, (int, float)):
        if label in {"Unsafe allocations", "Vehicles unserved"}:
            style_p = "green" if proposed <= baseline else "red"
        elif label in {"Vehicles served", "High/Critical served %", "Avg SoH allocated", "Avg suitability score"}:
            style_p = "green" if proposed >= baseline else "yellow"

    return label, f"[{style_p}]{p_str}[/{style_p}]" if style_p else p_str, b_str


def print_metrics_table(proposed: dict[str, object], baseline: dict[str, object]) -> None:
    table = Table(
        title="[bold]Allocation Results[/bold]",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        padding=(0, 1),
    )
    table.add_column("Metric", style="cyan", min_width=22)
    table.add_column("Proposed", justify="right", min_width=10)
    table.add_column("Baseline", justify="right", min_width=10)

    rows = [
        ("Vehicles served", "vehicles_served"),
        ("Vehicles unserved", "vehicles_unserved"),
        ("High/Critical served %", "high_critical_served_pct"),
        ("Unsafe allocations", "unsafe_allocations"),
        ("Avg SoH allocated", "avg_soh_allocated"),
        ("Avg suitability score", "avg_suitability_score"),
    ]
    for label, key in rows:
        p_val = proposed.get(key)
        b_val = baseline.get(key)
        lbl, p_fmt, b_fmt = _format_metric(label, p_val, b_val)
        table.add_row(lbl, p_fmt, b_fmt)

    console.print()
    console.print(table)
    console.print()


def print_file_list(files: list[Path], title: str) -> None:
    table = Table(title=title, show_header=True, header_style="bold", box=box.SIMPLE)
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("File", style="cyan")
    table.add_column("Type", justify="center", width=8)
    table.add_column("Size", justify="right", width=10)

    for i, f in enumerate(files, 1):
        size_kb = f.stat().st_size / 1024
        ext = f.suffix.upper().lstrip(".") or "?"
        table.add_row(str(i), f.name, ext, f"{size_kb:.1f} KB")

    console.print()
    console.print(table)
    console.print()


def print_outputs(paths: list[str]) -> None:
    table = Table(title="[bold]Generated outputs[/bold]", box=box.SIMPLE, show_header=True)
    table.add_column("File", style="green")
    for path in paths:
        table.add_row(Path(path).name)
    console.print(table)
    console.print()


def print_help() -> None:
    help_text = """
[bold cyan]Interactive[/bold cyan]
  battery-allocation              Open this menu

[bold cyan]Pipeline[/bold cyan]
  battery-allocation run          Auto-discover and run
  battery-allocation run --sample Use bundled datasets
  battery-allocation run -b fleet.xlsx -v demand.csv

[bold cyan]Data[/bold cyan]
  battery-allocation upload FILE  Upload CSV/Excel
  battery-allocation files        List data files
  battery-allocation validate     Validate without running

[bold cyan]Other[/bold cyan]
  battery-allocation serve        Start REST API
  battery-allocation version      Show version
"""
    console.print(
        Panel(
            help_text.strip(),
            title="[bold]Command reference[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print()


@contextmanager
def spinner(message: str) -> Iterator[None]:
    with Status(f"[bold cyan]{message}[/bold cyan]", console=console, spinner="dots") as status:
        yield
        status.update(f"[bold green]✓[/bold green] {message}")


def run_with_spinner(message: str, func: Callable[[], T]) -> T:
    with spinner(message):
        return func()
