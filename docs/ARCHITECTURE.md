# Architecture

## Overview

`battery-allocation` is a layered Python package for batch and API-driven battery health assessment and vehicle allocation at light EV swapping stations.

## Layers

```
┌─────────────────────────────────────────────────────────┐
│  CLI (typer)          REST API (FastAPI)                │
├─────────────────────────────────────────────────────────┤
│  Pipeline Runner  →  Exporters  →  Visualization      │
├─────────────────────────────────────────────────────────┤
│  Classification │ Scoring │ Allocation │ Twist Handler  │
├─────────────────────────────────────────────────────────┤
│  Data Loader + Pydantic CSV Validation                  │
├─────────────────────────────────────────────────────────┤
│  Config (YAML thresholds + pydantic-settings)           │
└─────────────────────────────────────────────────────────┘
```

## Module map

| Path | Responsibility |
|------|----------------|
| `config/settings.py` | Env-based settings, YAML loading |
| `core/models.py` | Domain entities |
| `core/classification.py` | Safe / Degraded / Unsafe rules |
| `core/scoring.py` | Suitability score 0–100 |
| `core/allocation.py` | Proposed + baseline algorithms |
| `core/twist.py` | Onsite twist parameter injection |
| `data/loader.py` | Validated CSV ingestion |
| `pipeline/runner.py` | Orchestration |
| `pipeline/exporters.py` | CSV/JSON outputs |
| `reporting/metrics.py` | KPIs + constraint verification |
| `reporting/visualization.py` | Matplotlib charts |
| `api/` | HTTP service |
| `cli/` | `battery-allocation` commands |

## Data flow

1. Load batteries and vehicle requests from CSV (validated).
2. Classify each battery once.
3. Run proposed allocation (priority + suitability).
4. Run baseline allocation (highest SOC first).
5. Verify constraints (no unsafe use, no duplicates, SOC minimums).
6. Export tables, metrics JSON, and charts.

## Deployment modes

| Mode | Entry | Use case |
|------|-------|----------|
| Batch CLI | `battery-allocation run` | Competition submission, offline analysis |
| API | `battery-allocation serve` | Station controller integration |
| Docker | `docker run` | Containerized pilot deployment |

## Configuration

- `config/thresholds.yaml` — classification and energy model parameters
- `config/default.yaml` — pipeline toggles
- `.env` / `BATTERY_ALLOCATION_*` — runtime paths and logging

## Extension points

- **Twist handler**: pass `--twist-json` or API body to filter inputs at event day
- **Thresholds YAML**: tune classification without code changes
- **Allocation strategies**: add new functions in `core/allocation.py`
