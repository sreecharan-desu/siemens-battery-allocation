# Benchmarks (19 Oct 2026)

| File | What |
|---|---|
| `bench_core.py` | Times classify/allocate at 1x, 10x and 50x the official dataset (clones rows with new IDs) |
| `k6-api.js` | Three sequential k6 scenarios: `/health` (50 VUs, 20 s), `/classifications/summary` (50 VUs, 20 s), `/pipeline/run` with `skip_visualizations` (8 VUs, 20 s) |
| `results-2026-10-19/` | Raw output: `core.txt`, `k6-output.txt`, `k6-summary.json`, `pytest-coverage.txt`, `pipeline-run.txt`, `environment.txt` |

## Environment

```
date_ist: 2026-10-19 08:37 UTC
host: single shared VM (load generator and server on the SAME box)
cpu: Intel(R) Xeon(R) Processor x 8 vCPU
ram: 15 GiB
os: Debian GNU/Linux 13 (trixie), kernel 6.12.94+
k6: k6 v0.54.0 (commit/baba871c8a, go1.23.1, linux/amd64)
server: uvicorn battery_allocation.api.app:create_app --factory --workers 4, Python 3.12.15
data: official CSVs (200 packs, 50 requests); no database
cold_start_ms: 1117
idle_rss_total_mb: 536.7 (processes: 6)
under_load_pipeline_rss_total_mb: 617.0 (processes: 6)
```

## Reproduce

```bash
source .venv/bin/activate && pip install -e ".[dev]"
python benchmarks/bench_core.py
uvicorn battery_allocation.api.app:create_app --factory --workers 4 --port 8000 &
k6 run --summary-export summary.json benchmarks/k6-api.js
```

Throughput = requests / scenario duration, using closed-loop VUs with no think time, so it's the saturation rate at that concurrency. Cold start = time from launching uvicorn to the first 200 from `/health`. Memory = summed RSS of the master and workers.
