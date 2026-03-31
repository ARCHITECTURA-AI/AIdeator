"""PH-C performance red-baseline tests (TC-P-200)."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="TC-P-200 locked until PH-C soak harness exists.")
def test_tc_p_200_long_running_soak_stability() -> None:
    """TC-P-200 -> NFR-001, LIVE-001, LIVE-002."""
    raise AssertionError("TC-P-200 not implemented yet")
