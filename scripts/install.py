#!/usr/bin/env python3
"""Cross-platform setup: venv + editable install. Works on macOS, Linux, and Windows."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def venv_python(venv_dir: Path) -> Path:
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def venv_cli(venv_dir: Path) -> Path:
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "battery-allocation.exe"
    return venv_dir / "bin" / "battery-allocation"


def run(cmd: list[str], *, cwd: Path) -> None:
    print(f"  → {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def find_python() -> str:
    return sys.executable


def print_success(venv_dir: Path) -> None:
    cli = venv_cli(venv_dir)
    system = platform.system()

    print("\n✓ Setup complete!\n")

    if system == "Windows":
        activate = venv_dir / "Scripts" / "Activate.ps1"
        print("Windows (PowerShell):")
        print(f"  {activate}")
        print("  battery-allocation\n")
        print("Windows (CMD):")
        print(f"  {venv_dir}\\Scripts\\activate.bat")
        print("  battery-allocation\n")
        print("Or run directly (no activate needed):")
        print(f"  {cli}")
    else:
        print("Mac / Linux:")
        print("  source .venv/bin/activate")
        print("  battery-allocation\n")
        print("Or run directly (no activate needed):")
        print(f"  {cli}")


def main() -> int:
    root = project_root()
    venv_dir = root / ".venv"
    python = find_python()

    print(f"Battery Allocation setup ({platform.system()})")
    print(f"Project: {root}\n")

    if not venv_dir.exists():
        print("Creating virtual environment...")
        run([python, "-m", "venv", str(venv_dir)], cwd=root)
    else:
        print("Virtual environment already exists — reusing .venv")

    py = venv_python(venv_dir)
    if not py.exists():
        print(f"Error: venv Python not found at {py}", file=sys.stderr)
        return 1

    print("Installing dependencies...")
    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "-q"], cwd=root)
    run([str(py), "-m", "pip", "install", "-e", ".[dev]", "-q"], cwd=root)

    print_success(venv_dir)

    if "--run" in sys.argv:
        print("\nLaunching interactive CLI...\n")
        os.execv(str(py), [str(py), "-m", "battery_allocation"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
