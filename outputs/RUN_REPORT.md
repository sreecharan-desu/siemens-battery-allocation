# Siemens Battery Allocation — Local Run Report

**Generated:** 2026-08-04  
**Project:** siemens-battery-allocation v1.0.0  
**Repository:** https://github.com/sreecharan-desu/siemens-battery-allocation (private)

---

## 1. Executive Summary

The battery health assessment and dynamic allocation system was run locally against the provided datasets (200 batteries, 50 vehicle requests). All safety constraints were satisfied. The proposed **Priority-Suitability** method matches the **Highest-SoC-First** baseline on total vehicles served (36/50) while improving High/Critical priority coverage, average SoH, and suitability scores.

| Check | Result |
|-------|--------|
| Tests | 25/25 passed |
| Code coverage | 88% |
| Ruff lint | Pass |
| Mypy | Pass |
| Constraint violations | 0 |
| Unsafe allocations | 0 |

---

## 2. Input Data

| Dataset | Records | File |
|---------|---------|------|
| Battery fleet | 200 packs | `data/Problem_1_Battery_Fleet_200_Packs.csv` |
| Vehicle demand | 50 requests | `data/Problem_1_Vehicle_Demand_50_Requests.csv` |

---

## 3. Battery Classification

Every battery was classified into exactly one category.

| Category | Count | Avg Suitability Score |
|----------|------:|----------------------:|
| Safe and Available | 128 | 75.57 |
| Degraded but Usable | 58 | 61.77 |
| Unsafe / Quarantine | 14 | 60.19 |
| **Total** | **200** | — |

**14 batteries** were flagged as Unsafe / Quarantine and excluded from allocation. Full list: `outputs/quarantine_report.csv`.

---

## 4. Allocation Results

### 4.1 Proposed Method (Priority-Suitability)

| Metric | Value |
|--------|------:|
| Vehicles served | 36 |
| Vehicles unserved | 14 |
| High + Critical served | 73.08% |
| Unsafe allocations | 0 |
| Avg SoH of allocated batteries | 90.37% |
| Avg suitability score | 84.54 |

### 4.2 Baseline (Highest-SoC-First)

| Metric | Value |
|--------|------:|
| Vehicles served | 36 |
| Vehicles unserved | 14 |
| High + Critical served | 69.23% |
| Unsafe allocations | 0 |
| Avg SoH of allocated batteries | 80.49% |
| Avg suitability score | 76.80 |

### 4.3 Method Comparison

| Metric | Proposed | Baseline | Delta |
|--------|----------|----------|-------|
| Vehicles served | 36 | 36 | 0 |
| High/Critical served (%) | 73.08 | 69.23 | **+3.85** |
| Avg SoH allocated | 90.37 | 80.49 | **+9.88** |
| Avg suitability score | 84.54 | 76.80 | **+7.74** |
| Unsafe allocations | 0 | 0 | 0 |

**36 of 36** served vehicles received a different battery assignment under the proposed method vs baseline, demonstrating materially different allocation strategy while maintaining the same serve count.

---

## 5. Service by Priority (Proposed Method)

| Priority | Served | Total | Serve Rate |
|----------|-------:|------:|-----------:|
| Critical | 2 | 4 | 50.0% |
| High | 17 | 22 | 77.3% |
| Normal | 17 | 24 | 70.8% |

---

## 6. Constraint Verification

All mandatory verification rules passed:

- [x] No unsafe/quarantined battery was allocated
- [x] No battery assigned to more than one vehicle
- [x] No vehicle received more than one battery
- [x] Allocated battery SOC met each vehicle's minimum acceptable SOC
- [x] Results are reproducible from submitted datasets and code

---

## 7. Quality Gates (Local)

```
pytest tests/          → 25 passed, 88% coverage
ruff check src tests   → All checks passed
mypy src/battery_allocation → Success, no issues
battery-allocation run → Pipeline completed successfully
```

---

## 8. Generated Artifacts

| File | Description |
|------|-------------|
| `outputs/battery_classifications.csv` | Per-battery category and suitability score |
| `outputs/quarantine_report.csv` | 14 unsafe/quarantined batteries |
| `outputs/allocations_proposed.csv` | Proposed method assignments |
| `outputs/allocations_baseline_highest_soc.csv` | Baseline assignments |
| `outputs/metrics_report.json` | Quantitative comparison (machine-readable) |
| `outputs/01_battery_classification.png` | Classification distribution chart |
| `outputs/02_suitability_score_distribution.png` | Score histogram by category |
| `outputs/03_allocation_by_priority_proposed.png` | Served vs unserved by priority |
| `outputs/04_method_comparison.png` | Proposed vs baseline metrics |
| `outputs/05_quarantine_batteries.png` | Identified quarantine batteries |

---

## 9. Commands Used

```bash
cd siemens-battery-allocation
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v --cov=battery_allocation
battery-allocation run
```

---

## 10. Conclusion

The system is fully operational locally. The proposed Priority-Suitability allocator delivers better battery health outcomes and priority coverage than the Highest-SoC-First baseline, with zero safety violations. All mandatory quantitative outputs and visualizations were generated successfully.
