# Battery Health Assessment and Dynamic Allocation

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/sreecharan-desu/siemens-battery-allocation/releases/tag/v1.0.0)
[![CI](https://github.com/sreecharan-desu/siemens-battery-allocation/actions/workflows/ci.yml/badge.svg)](https://github.com/sreecharan-desu/siemens-battery-allocation/actions/workflows/ci.yml)

**Production-grade battery allocation for light EV battery-swapping stations.**

Classifies battery health, scores suitability, and assigns packs to vehicle requests under safety and priority constraints. Built for the Siemens Energy / IMECE India 2026 Brain Bolt Engineers Sprint. Includes a CLI, REST API, Docker image, and CI pipeline with full test coverage.

**Repository:** [github.com/sreecharan-desu/siemens-battery-allocation](https://github.com/sreecharan-desu/siemens-battery-allocation)

## Features

- Battery classification (Safe / Degraded / Unsafe)
- Suitability scoring (0–100)
- Priority-aware allocation + Highest-SoC-First baseline
- Constraint verification and quantitative metrics
- CLI, REST API, Docker, CI pipeline
- Config-driven thresholds (YAML + environment variables)
- Onsite twist handler for event-day constraints

## Prerequisites

- Python 3.11 or newer
- pip
- Optional: Docker for containerized deployment

## Quick start

```bash
git clone https://github.com/sreecharan-desu/siemens-battery-allocation.git
cd siemens-battery-allocation

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

battery-allocation run
```

## Commands

| Command | Description |
|---------|-------------|
| `battery-allocation run` | Full batch pipeline |
| `battery-allocation run --skip-viz` | Pipeline without charts |
| `battery-allocation run --twist-json '{"min_soh_percent":75}'` | Apply onsite twist |
| `battery-allocation serve` | Start REST API |
| `pytest tests/ -v` | Run test suite |
| `ruff check src tests` | Lint |
| `mypy src/battery_allocation` | Type check |

## Docker

```bash
docker build -t battery-allocation .
docker run -p 8000:8000 battery-allocation
```

## Configuration

Copy `.env.example` to `.env` and set:

```env
BATTERY_ALLOCATION_LOG_LEVEL=INFO
BATTERY_ALLOCATION_BATTERY_CSV=data/Problem_1_Battery_Fleet_200_Packs.csv
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
├── .github/workflows/ci.yml      # Lint, type-check, test, smoke run
├── config/                       # YAML thresholds and pipeline toggles
├── data/                         # Input CSV datasets
├── docs/                         # Architecture, method, API docs
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
