# Battery Health Assessment and Dynamic Allocation

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.2.0-green.svg)](https://github.com/sreecharan-desu/siemens-battery-allocation/releases)
[![CI](https://github.com/sreecharan-desu/siemens-battery-allocation/actions/workflows/ci.yml/badge.svg)](https://github.com/sreecharan-desu/siemens-battery-allocation/actions/workflows/ci.yml)

**Production-grade battery allocation for light EV battery-swapping stations.**

Classifies battery health, scores suitability, and assigns packs to vehicle requests under safety and priority constraints. Built for the Siemens Energy / IMECE India 2026 Brain Bolt Engineers Sprint.

**Repository:** [github.com/sreecharan-desu/siemens-battery-allocation](https://github.com/sreecharan-desu/siemens-battery-allocation)

## One-line setup

**Prerequisite:** [Python 3.11+](https://www.python.org/downloads/) installed on your machine.

### All platforms (recommended)

Uses the cross-platform installer — same command everywhere:

```bash
git clone https://github.com/sreecharan-desu/siemens-battery-allocation.git && cd siemens-battery-allocation && python scripts/install.py
```

Add `--run` to install and launch the interactive CLI immediately:

```bash
git clone https://github.com/sreecharan-desu/siemens-battery-allocation.git && cd siemens-battery-allocation && python scripts/install.py --run
```

### Platform shortcuts

| OS | Setup command | Activate & run |
|----|---------------|----------------|
| **macOS / Linux** | `./scripts/install.sh` | `source .venv/bin/activate` then `battery-allocation` |
| **Windows (PowerShell)** | `.\scripts\install.ps1` | `.\.venv\Scripts\Activate.ps1` then `battery-allocation` |
| **Windows (CMD)** | `scripts\install.bat` | `.venv\Scripts\activate.bat` then `battery-allocation` |

**No activate needed** — run the CLI directly after setup:

```bash
# macOS / Linux
.venv/bin/battery-allocation

# Windows
.venv\Scripts\battery-allocation.exe
```

## Interactive CLI

Run `battery-allocation` with no arguments — a clean, menu-driven experience:

- **Active data panel** — shows your last-used battery & vehicle files
- **Guided file picker** — browse, upload, or type a path
- **Live progress spinner** — during pipeline runs
- **Color-coded results** — proposed vs baseline metrics at a glance
- **Confirm before quit** — no accidental exits

```
  ⚡ Battery Allocation  v1.2.0
     Classify  ·  Score  ·  Allocate  ·  Report

  ┌─ Active data ─────────────────────────┐
  │ Battery   Problem_1_Battery_Fleet...  │
  │ Vehicle   Problem_1_Vehicle_Demand... │
  └───────────────────────────────────────┘

  Key │ Action        │ Description
  ────┼───────────────┼──────────────────────────
   1  │ Run pipeline  │ Use your CSV or Excel files
   2  │ Quick demo    │ Bundled sample competition data
   ...
```

## Quick commands

| Command | Description |
|---------|-------------|
| `battery-allocation` | Interactive menu (default) |
| `battery-allocation run` | Run pipeline (auto-discovers data files) |
| `battery-allocation run --sample` | Use bundled competition datasets |
| `battery-allocation run -b fleet.xlsx -v demand.csv` | Explicit file paths |
| `battery-allocation upload ./mydata.xlsx` | Upload CSV/Excel to `data/uploads/` |
| `battery-allocation files` | List discoverable data files |
| `battery-allocation validate --sample` | Validate files without running pipeline |
| `battery-allocation serve` | Start REST API |
| `battery-allocation version` | Show version |

## Data files

No hardcoded paths. The CLI discovers files automatically from:

1. Explicit `-b` / `-v` flags
2. Saved config (`.battery-allocation.json`)
3. `data/uploads/` then `data/` (filename hints: *battery*, *fleet*, *vehicle*, *demand*)
4. Bundled sample datasets (`--sample` or menu option 2)

Supported formats: **CSV**, **Excel** (`.xlsx`, `.xls`)

## Features

- Battery classification (Safe / Degraded / Unsafe)
- Suitability scoring (0–100)
- Priority-aware allocation + Highest-SoC-First baseline
- Constraint verification and quantitative metrics
- Interactive CLI, REST API, Docker, CI pipeline
- Config-driven thresholds (YAML + environment variables)
- Onsite twist handler for event-day constraints

## Docker

```bash
docker build -t battery-allocation .
docker run -p 8000:8000 battery-allocation
```

## Configuration

Copy `.env.example` to `.env` and set optional overrides:

```env
BATTERY_ALLOCATION_LOG_LEVEL=INFO
BATTERY_ALLOCATION_OUTPUT_DIR=outputs
```

Tune classification thresholds in `config/thresholds.yaml` without code changes.

## Outputs

| File | Description |
|------|-------------|
| `battery_classifications.csv` | Per-battery category and score |
| `quarantine_report.csv` | Unsafe batteries only |
| `allocations_proposed.csv` | Proposed method assignments |
| `allocations_baseline_highest_soc.csv` | Baseline assignments |
| `metrics_report.json` | Quantitative comparison |
| `01–05_*.png` | Visualizations |

## Project structure

```
siemens-battery-allocation/
├── scripts/install.py            # Cross-platform setup (macOS, Linux, Windows)
├── scripts/install.sh            # macOS / Linux shortcut
├── scripts/install.ps1           # Windows PowerShell shortcut
├── scripts/install.bat           # Windows CMD shortcut
├── config/                       # YAML thresholds and pipeline toggles
├── data/                         # Sample datasets + uploads/
├── src/battery_allocation/       # Main package
├── tests/                        # Unit and integration tests
├── Dockerfile
└── pyproject.toml
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Method](docs/METHOD.md)
- [API](docs/API.md)
- [Problem statement](docs/problem_statement.pdf)

## Quality gates

CI runs on Python 3.11 and 3.12:

- Ruff lint
- Mypy strict mode
- Pytest with ≥80% coverage
- Pipeline smoke test

## License

Proprietary — Siemens Energy / IMECE India 2026 competition submission. All rights reserved.
