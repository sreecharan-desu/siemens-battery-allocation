# Method Description

## Problem

A battery-swapping station must assign at most one suitable battery per vehicle request while respecting safety, SOC, and operational constraints. Selecting only by highest SOC can waste healthy packs, assign degraded units inappropriately, and miss priority vehicles.

## Classification

Each battery is assigned **exactly one** category:

| Category | Criteria (configurable in `config/thresholds.yaml`) |
|----------|------------------------------------------------------|
| **Unsafe / Quarantine** | Station `REVIEW/QUARANTINE`, or SOH/temp/resistance/imbalance/24h-temp beyond unsafe thresholds |
| **Degraded but Usable** | Not unsafe, but SOH/resistance/imbalance/cycles exceed degraded thresholds |
| **Safe and Available** | All parameters within safe limits |

Unsafe batteries are **never** allocated.

## Suitability Score (0–100)

Composite from five health parameters:

| Component | Weight | Logic |
|-----------|--------|-------|
| SOH | 30 | Higher is better |
| SOC | 25 | Higher is better |
| Internal resistance | 20 | Lower is better |
| Cell voltage imbalance | 15 | Lower is better |
| Temperature | 10 | Optimal 25–35°C |

## Proposed allocation (Priority-Suitability)

1. Sort requests by priority (Critical → High → Normal), then arrival time.
2. For each request, build eligible batteries:
   - Not unsafe
   - SOC ≥ vehicle minimum
   - Available energy ≥ required trip energy
3. Score candidates: suitability + energy margin + category bonus + SOC balance.
4. Assign highest-scoring unused battery.

## Baseline (Highest-SoC-First)

Process requests in arrival order; assign highest-SOC eligible unused battery.

## Energy model

Required energy = `range_km × vehicle_kWh_per_km × load_multiplier` (from YAML config).

## Onsite twist (30%)

The `core/twist.py` module accepts runtime filters (e.g. minimum SOH, max temperature) via:

```bash
battery-allocation run --twist-json '{"name":"pilot","min_soh_percent":75}'
```

or the API `POST /pipeline/run` with a `twist` object. Core allocation logic remains unchanged; twist filters inputs before classification/allocation.

## Validation

Every run verifies:

1. No unsafe allocations
2. No duplicate battery assignments
3. One battery max per vehicle
4. SOC minimum satisfied

## Comparison metrics

- Vehicles served / unserved
- High + Critical priority served (%)
- Unsafe allocations (must be 0)
- Average SoH of allocated batteries
- Average suitability score of allocated batteries
