# Battery Health Assessment and Dynamic Allocation

[![CI](https://github.com/sreecharan-desu/siemens-battery-allocation/actions/workflows/ci.yml/badge.svg)](https://github.com/sreecharan-desu/siemens-battery-allocation/actions/workflows/ci.yml)

Classifies light-EV battery packs (Safe / Degraded / Unsafe), gives each a 0–100 suitability score, and assigns packs to incoming vehicle requests under safety and priority constraints. Built for the Siemens Energy / IMECE India 2026 Brain Bolt Engineers Sprint. Interfaces: CLI, REST API (FastAPI) and Docker.

## Results on the official dataset (200 packs, 50 requests)

From `battery-allocation run --sample --skip-viz` ([raw output](benchmarks/results-2026-10-19/pipeline-run.txt)):

| Metric | Proposed (priority + suitability) | Baseline (highest SoC first) |
|---|---|---|
| Vehicles served | 36 / 50 | 36 / 50 |
| High/critical-priority served | **73.1%** | 69.2% |
| Unsafe packs allocated | 0 | 0 |
| Avg state of health of allocated packs | **90.4%** | 80.5% |
| Avg suitability score | **84.5** | 76.8 |

## How it works

```
data/loader      CSV/Excel -> typed models (auto-discovers files)
core/            classification -> scoring -> allocation (+ baseline), on-site "twist" constraints
pipeline/        run, verify constraints, export CSV/JSON/PNG to outputs/
cli/ , api/      Typer CLI and FastAPI (/health, /pipeline/run, /classifications/summary, /requests/summary)
config/          thresholds.yaml, default.yaml (overridable by env vars)
```

Method details: [docs/METHOD.md](docs/METHOD.md) · Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · API: [docs/API.md](docs/API.md) · Deck: [PDF](docs/Siemens_Battery_Allocation_Presentation.pdf)

## Setup

Python 3.11+.

```bash
git clone https://github.com/sreecharan-desu/siemens-battery-allocation.git && cd siemens-battery-allocation
python scripts/install.py            # creates .venv and installs (install.sh / install.ps1 / install.bat also work)
.venv/bin/battery-allocation          # interactive menu
.venv/bin/battery-allocation run --sample
.venv/bin/battery-allocation serve    # REST API on :8000
```

Docker: `docker build -t battery-allocation . && docker run -p 8000:8000 battery-allocation`

| Command | Purpose |
|---|---|
| `run [-b fleet.xlsx -v demand.csv] [--sample] [--skip-viz]` | Run the pipeline |
| `upload <file>`, `files`, `validate` | Manage and check input files |
| `serve`, `version` | Start the API, print the version |

Outputs go to `outputs/`: classifications, quarantine report, proposed and baseline allocations, `metrics_report.json`, and charts.

## Tests

```bash
pytest --cov=battery_allocation      # CI also runs ruff, mypy --strict and a pipeline smoke test on 3.11 and 3.12
```

Measured 19 Oct 2026: **58 passed in 7.7 s, 81.5% coverage** (CI gate is 80%). [Raw output](benchmarks/results-2026-10-19/pytest-coverage.txt).

## Performance (measured)

One 8 vCPU / 15 GiB VM (Intel Xeon), Python 3.12, single run. The load generator ran on the same machine. Method and environment: [benchmarks/README.md](benchmarks/README.md).

**Algorithm** (`benchmarks/bench_core.py`, [raw](benchmarks/results-2026-10-19/core.txt)). The larger fleets are the official rows cloned 10x and 50x:

| Fleet / requests | classify p50 | allocate (proposed) p50 / p95 | allocate (baseline) p50 |
|---|---|---|---|
| 200 / 50 (official) | 0.39 ms | **4.3 ms / 5.0 ms** | 2.7 ms |
| 2,000 / 500 | 3.7 ms | 439 ms / 468 ms | 281 ms |
| 10,000 / 2,500 | 19.7 ms | 11.6 s / 11.7 s | 7.7 s |

Peak Python heap for the 10,000-pack run: 7.1 MB.

**HTTP API** (`uvicorn --workers 4`, k6 closed-loop VUs, [k6 output](benchmarks/results-2026-10-19/k6-output.txt), [summary JSON](benchmarks/results-2026-10-19/k6-summary.json)):

| Endpoint | Concurrency (VUs) | Requests | Throughput (req/s) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Error rate |
|---|---|---|---|---|---|---|---|---|
| `GET /health` | 50 | 308,771 | 15,439 | 3.0 | 5.3 | 7.3 | 75.3 | 0.00% |
| `GET /classifications/summary` | 50 | 8,671 | 434 | 110.7 | 184.7 | 216.8 | 396.8 | 0.00% |
| `POST /pipeline/run` | 8 | 3,393 | 170 | 45.9 | 82.1 | 96.0 | 141.2 | 0.00% |

On that hardware, the API sustained **170 full pipeline runs/s at p95 82 ms** on the official dataset (8 VUs, no charts). Cold start (process launch to first healthy response): 1.1 s. RSS for master + 4 workers: 537 MB idle, 617 MB under load.

## Known issues

- **Allocation is O(requests x packs).** Each request rescans every pack, so the runtime grows about 100x when the input grows 10x (measured above). That's fine for one station (200 packs). A per-request candidate index or a heap would be needed for fleet-scale inputs.
- `GET /classifications/summary` re-reads and re-classifies the CSV on every call (434 req/s, p95 185 ms), which makes it slower than `/pipeline/run`. It should be cached.
- `POST /pipeline/run` accepts arbitrary `battery_csv` / `output_dir` paths from the request body. Don't expose the API publicly without restricting those paths.
- License: proprietary competition submission (see `pyproject.toml`). All rights reserved.
