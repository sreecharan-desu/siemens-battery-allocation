"""Time the core pipeline (classify -> score -> allocate) on the official dataset and on
synthetic fleets built by cloning the official rows (new IDs, same values).

Run: python benchmarks/bench_core.py > benchmarks/results-<date>/core.txt
"""
from __future__ import annotations

import dataclasses
import platform
import statistics
import sys
import time
import tracemalloc

from battery_allocation.core.allocation import allocate_highest_soc_first, allocate_priority_suitability
from battery_allocation.core.classification import classify_fleet
from battery_allocation.data.loader import load_batteries, load_vehicle_requests


def clone(items, factor, id_field):
    out = []
    for k in range(factor):
        for it in items:
            out.append(dataclasses.replace(it, **{id_field: f"{getattr(it, id_field)}-{k}"}) if dataclasses.is_dataclass(it)
                       else it.model_copy(update={id_field: f"{getattr(it, id_field)}-{k}"}))
    return out


def timeit(fn, repeat):
    xs = []
    for _ in range(repeat):
        t = time.perf_counter(); fn(); xs.append((time.perf_counter() - t) * 1000)
    xs.sort()
    return statistics.median(xs), xs[max(0, int(len(xs) * 0.95) - 1)], xs[-1]


def main() -> None:
    print(f"python {platform.python_version()} on {platform.machine()}, {platform.processor() or 'cpu n/a'}")
    bats, reqs = load_batteries(), load_vehicle_requests()
    print(f"{'scale':>6} {'batteries':>9} {'requests':>8} | {'stage':<32} {'runs':>4} {'p50 ms':>9} {'p95 ms':>9} {'max ms':>9} | allocated")
    for factor, repeat in ((1, 200), (10, 20), (50, 5)):
        b = clone(bats, factor, "battery_id"); r = clone(reqs, factor, "request_id")
        cls = classify_fleet(b)
        stages = {
            "classify_fleet": lambda: classify_fleet(b),
            "allocate_priority_suitability": lambda: allocate_priority_suitability(b, r, cls),
            "allocate_highest_soc_first (baseline)": lambda: allocate_highest_soc_first(b, r, cls),
        }
        for name, fn in stages.items():
            p50, p95, mx = timeit(fn, repeat)
            res = fn() if name.startswith("allocate") else None
            alloc = sum(1 for a in res if getattr(a, "battery_id", None)) if res is not None else "-"
            print(f"{factor:>5}x {len(b):>9} {len(r):>8} | {name:<32} {repeat:>4} {p50:>9.2f} {p95:>9.2f} {mx:>9.2f} | {alloc}")
    tracemalloc.start()
    b = clone(bats, 50, "battery_id"); r = clone(reqs, 50, "request_id")
    allocate_priority_suitability(b, r, classify_fleet(b))
    cur, peak = tracemalloc.get_traced_memory()
    print(f"peak python heap for 50x classify+allocate: {peak/1e6:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())
