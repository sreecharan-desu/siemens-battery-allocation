"""Tests for cross-platform install script."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_install_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "install.py"
    spec = importlib.util.spec_from_file_location("install_script", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_install_scripts_exist(project_root: Path):
    scripts = project_root / "scripts"
    for name in ("install.py", "install.sh", "install.ps1", "install.bat"):
        assert (scripts / name).is_file(), f"missing {name}"


def test_project_root_points_to_repo():
    install = _load_install_module()
    root = install.project_root()
    assert (root / "pyproject.toml").is_file()
    assert (root / "data").is_dir()


def test_venv_paths_after_setup(project_root: Path):
    install = _load_install_module()
    venv = project_root / ".venv"
    if not venv.exists():
        return
    assert install.venv_python(venv).exists()
    assert install.venv_cli(venv).exists()
