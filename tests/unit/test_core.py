"""Unit tests for core domain logic."""

from __future__ import annotations

from battery_allocation.core.allocation import (
    allocate_highest_soc_first,
    allocate_priority_suitability,
)
from battery_allocation.core.classification import classify_battery, classify_fleet, is_allocatable
from battery_allocation.core.models import Battery, BatteryCategory, VehiclePriority
from battery_allocation.core.scoring import compute_suitability_score
from battery_allocation.data.loader import load_batteries, load_vehicle_requests
from battery_allocation.reporting.metrics import compute_metrics, verify_allocations


class TestDataLoading:
    def test_load_batteries_count(self):
        assert len(load_batteries()) == 200

    def test_load_vehicle_requests_count(self):
        assert len(load_vehicle_requests()) == 50

    def test_battery_fields(self):
        b = load_batteries()[0]
        assert b.battery_id.startswith("BAT-")
        assert b.chemistry == "LFP"

    def test_request_priority_parsing(self):
        priorities = {r.priority for r in load_vehicle_requests()}
        assert VehiclePriority.CRITICAL in priorities
        assert VehiclePriority.HIGH in priorities
        assert VehiclePriority.NORMAL in priorities


class TestScoring:
    def test_score_in_range(self, sample_battery: Battery):
        score = compute_suitability_score(sample_battery)
        assert 0 <= score <= 100

    def test_higher_soh_higher_score(self, sample_battery: Battery):
        low = Battery(**{**sample_battery.__dict__, "state_of_health_percent": 60.0})
        high = Battery(**{**sample_battery.__dict__, "state_of_health_percent": 95.0})
        assert compute_suitability_score(high) > compute_suitability_score(low)


class TestClassification:
    def test_safe_battery(self, sample_battery: Battery):
        cls = classify_battery(sample_battery)
        assert cls.category == BatteryCategory.SAFE_AVAILABLE
        assert is_allocatable(cls)

    def test_quarantine_station_status(self, sample_battery: Battery):
        quarantined = Battery(**{**sample_battery.__dict__, "station_status": "REVIEW/QUARANTINE"})
        cls = classify_battery(quarantined)
        assert cls.category == BatteryCategory.UNSAFE_QUARANTINE
        assert not is_allocatable(cls)

    def test_every_battery_classified_once(self):
        classifications = classify_fleet(load_batteries())
        assert len(classifications) == 200

    def test_quarantined_batteries_in_dataset(self):
        classifications = classify_fleet(load_batteries())
        unsafe = [c for c in classifications.values() if c.category == BatteryCategory.UNSAFE_QUARANTINE]
        assert len(unsafe) >= 12


class TestAllocation:
    def test_no_duplicate_battery_assignment(self):
        batteries = load_batteries()
        requests = load_vehicle_requests()
        classifications = classify_fleet(batteries)

        for fn in [allocate_priority_suitability, allocate_highest_soc_first]:
            allocations = fn(batteries, requests, classifications)
            used = [a.battery_id for a in allocations if a.served and a.battery_id]
            assert len(used) == len(set(used))

    def test_no_unsafe_allocations(self):
        batteries = load_batteries()
        requests = load_vehicle_requests()
        classifications = classify_fleet(batteries)

        for fn in [allocate_priority_suitability, allocate_highest_soc_first]:
            allocations = fn(batteries, requests, classifications)
            assert verify_allocations(allocations, batteries, requests, classifications) == []

    def test_soc_constraint_respected(self):
        batteries = load_batteries()
        requests = load_vehicle_requests()
        classifications = classify_fleet(batteries)
        battery_map = {b.battery_id: b for b in batteries}
        request_map = {r.request_id: r for r in requests}

        allocations = allocate_priority_suitability(batteries, requests, classifications)
        for alloc in allocations:
            if alloc.served and alloc.battery_id:
                assert battery_map[alloc.battery_id].state_of_charge_percent >= (
                    request_map[alloc.request_id].minimum_acceptable_soc_percent
                )

    def test_at_most_one_battery_per_vehicle(self):
        batteries = load_batteries()
        requests = load_vehicle_requests()
        classifications = classify_fleet(batteries)
        allocations = allocate_priority_suitability(batteries, requests, classifications)
        assert len(allocations) == len(requests)


class TestMetrics:
    def test_metrics_computation(self):
        batteries = load_batteries()
        requests = load_vehicle_requests()
        classifications = classify_fleet(batteries)
        allocations = allocate_priority_suitability(batteries, requests, classifications)
        metrics = compute_metrics("Test", allocations, batteries, requests, classifications)
        assert metrics.vehicles_served + metrics.vehicles_unserved == 50
        assert metrics.unsafe_allocations == 0

    def test_proposed_serves_high_critical_well(self):
        batteries = load_batteries()
        requests = load_vehicle_requests()
        classifications = classify_fleet(batteries)
        proposed = allocate_priority_suitability(batteries, requests, classifications)
        baseline = allocate_highest_soc_first(batteries, requests, classifications)
        proposed_m = compute_metrics("Proposed", proposed, batteries, requests, classifications)
        baseline_m = compute_metrics("Baseline", baseline, batteries, requests, classifications)
        assert proposed_m.high_critical_served_pct >= baseline_m.high_critical_served_pct
