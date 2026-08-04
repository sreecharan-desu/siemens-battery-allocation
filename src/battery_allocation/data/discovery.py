"""Discover and resolve battery / vehicle data files dynamically."""

from __future__ import annotations

import json
import re
from pathlib import Path

from battery_allocation.data.spreadsheet import is_supported_data_file

SAMPLE_BATTERY = "Problem_1_Battery_Fleet_200_Packs.csv"
SAMPLE_VEHICLE = "Problem_1_Vehicle_Demand_50_Requests.csv"

BATTERY_HINTS = ("battery", "fleet", "pack")
VEHICLE_HINTS = ("vehicle", "demand", "request")


def data_search_dirs(project_root: Path) -> list[Path]:
    return [
        project_root / "data" / "uploads",
        project_root / "data",
        project_root,
    ]


def uploads_dir(project_root: Path) -> Path:
    path = project_root / "data" / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path(project_root: Path) -> Path:
    return project_root / ".battery-allocation.json"


def load_user_config(project_root: Path) -> dict[str, str]:
    path = config_path(project_root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def save_user_config(project_root: Path, battery: Path | None, vehicle: Path | None) -> None:
    cfg = load_user_config(project_root)
    if battery:
        cfg["battery_file"] = str(battery.resolve())
    if vehicle:
        cfg["vehicle_file"] = str(vehicle.resolve())
    config_path(project_root).write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _score_filename(name: str, hints: tuple[str, ...]) -> int:
    lower = name.lower()
    score = 0
    for hint in hints:
        if hint in lower:
            score += 2
    if lower.endswith((".csv", ".xlsx", ".xls")):
        score += 1
    return score


def discover_files(project_root: Path) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for directory in data_search_dirs(project_root):
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir()):
            if is_supported_data_file(path):
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    files.append(path)
    return files


def guess_battery_files(project_root: Path) -> list[Path]:
    files = discover_files(project_root)
    scored = [(f, _score_filename(f.name, BATTERY_HINTS)) for f in files]
    return [f for f, s in sorted(scored, key=lambda x: (-x[1], x[0].name)) if s > 0]


def guess_vehicle_files(project_root: Path) -> list[Path]:
    files = discover_files(project_root)
    scored = [(f, _score_filename(f.name, VEHICLE_HINTS)) for f in files]
    return [f for f, s in sorted(scored, key=lambda x: (-x[1], x[0].name)) if s > 0]


def sample_battery_path(project_root: Path) -> Path:
    return project_root / "data" / SAMPLE_BATTERY


def sample_vehicle_path(project_root: Path) -> Path:
    return project_root / "data" / SAMPLE_VEHICLE


def resolve_data_file(
    project_root: Path,
    kind: str,
    explicit: Path | None = None,
    use_sample: bool = False,
) -> Path:
    """Resolve battery or vehicle file: explicit > saved config > auto-discover > sample."""
    if explicit is not None:
        path = explicit.expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"{kind.title()} file not found: {path}")
        if not is_supported_data_file(path):
            raise ValueError(f"Unsupported file type: {path.suffix}")
        return path

    if use_sample:
        sample = sample_battery_path(project_root) if kind == "battery" else sample_vehicle_path(project_root)
        if sample.exists():
            return sample
        raise FileNotFoundError(f"Sample {kind} file not found: {sample}")

    cfg = load_user_config(project_root)
    cfg_key = "battery_file" if kind == "battery" else "vehicle_file"
    if cfg_key in cfg:
        saved = Path(cfg[cfg_key])
        if saved.exists():
            return saved

    guesses = guess_battery_files(project_root) if kind == "battery" else guess_vehicle_files(project_root)
    if len(guesses) == 1:
        return guesses[0]
    if guesses:
        return guesses[0]

    sample = sample_battery_path(project_root) if kind == "battery" else sample_vehicle_path(project_root)
    if sample.exists():
        return sample

    raise FileNotFoundError(
        f"No {kind} data file found. Upload one with: battery-allocation upload <file>"
    )


def copy_upload(src: Path, project_root: Path) -> Path:
    """Copy an uploaded file into data/uploads/ and return destination path."""
    src = src.expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"File not found: {src}")
    if not is_supported_data_file(src):
        raise ValueError(f"Unsupported file type: {src.suffix}. Use CSV or Excel.")

    dest_dir = uploads_dir(project_root)
    safe_name = re.sub(r"[^\w.\-]", "_", src.name)
    dest = dest_dir / safe_name
    dest.write_bytes(src.read_bytes())
    return dest
