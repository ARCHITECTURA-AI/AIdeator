"""PH-B performance red-baseline smoke tests (TC-P-100+)."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="TC-P-100 locked until PH-B perf harness is implemented.")
def test_tc_p_100_latency_regression_vs_ph_a_baseline() -> None:
    """TC-P-100 -> NFR-001."""
    raise AssertionError("TC-P-100 not implemented yet")


@pytest.mark.skip(reason="TC-P-101 locked until PH-B concurrency harness is implemented.")
def test_tc_p_101_parallel_run_throughput_bound() -> None:
    """TC-P-101 -> NFR-001, NFR-002."""
    raise AssertionError("TC-P-101 not implemented yet")
