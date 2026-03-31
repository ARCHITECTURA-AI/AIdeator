"""Performance and load-smoke tests tracked in red baseline."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="TC-P-001 locked for implementation phase with perf harness.")
def test_tc_p_001_low_tier_p95_latency_bound() -> None:
    """TC-P-001 -> NFR-001."""
    raise AssertionError("TC-P-001 not implemented yet")


@pytest.mark.skip(reason="TC-P-002 locked for implementation phase with cloud-mode harness.")
def test_tc_p_002_medium_tier_p95_latency_bound() -> None:
    """TC-P-002 -> NFR-001."""
    raise AssertionError("TC-P-002 not implemented yet")


@pytest.mark.skip(reason="TC-P-003 locked for implementation phase with watchdog benchmark harness.")
def test_tc_p_003_watchdog_overhead_bound() -> None:
    """TC-P-003 -> LIVE-002, NFR-001."""
    raise AssertionError("TC-P-003 not implemented yet")
