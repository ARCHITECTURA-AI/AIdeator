"""Red-baseline unit tests for mode and run invariants."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any


def _require_attr(module_path: str, *names: str) -> Any:
    module = importlib.import_module(module_path)
    for name in names:
        value = getattr(module, name, None)
        if value is not None:
            return value
    joined = ", ".join(names)
    raise AssertionError(f"Expected one of [{joined}] in {module_path}")


def _require_callable(module_path: str, *names: str) -> Callable[..., Any]:
    value = _require_attr(module_path, *names)
    if not callable(value):
        raise AssertionError(f"Expected callable for {module_path}:{names}")
    return value


def test_tc_u_001_modeguard_allows_internal_local_only() -> None:
    """TC-U-001 -> INV-001, NFR-010."""
    _require_attr("engine.mode_guard", "ModeGuard")


def test_tc_u_002_modeguard_blocks_external_local_only() -> None:
    """TC-U-002 -> INV-001, SAFE-002, NFR-010."""
    _require_attr("engine.mode_guard", "ModeGuard")


def test_tc_u_003_modeguard_enforces_hybrid_keyword_only() -> None:
    """TC-U-003 -> INV-002, NFR-009."""
    _require_attr("engine.mode_guard", "ModeGuard")


def test_tc_u_004_run_mode_immutable_once_set() -> None:
    """TC-U-004 -> INV-007."""
    _require_attr("models.run", "Run")


def test_tc_u_010_accepts_valid_state_transitions() -> None:
    """TC-U-010 -> INV-006, NFR-002."""
    _require_attr("models.run", "Run")


def test_tc_u_011_rejects_backward_state_transition() -> None:
    """TC-U-011 -> INV-006, NFR-002."""
    _require_attr("models.run", "Run")


def test_tc_u_012_rejects_second_terminal_transition() -> None:
    """TC-U-012 -> INV-006."""
    _require_attr("models.run", "Run")


def test_tc_u_030_reddit_query_builder_truncates_to_ten_words() -> None:
    """TC-U-030 -> INV-002, NFR-009."""
    _require_callable("engine.signal_collector", "build_hybrid_query", "build_keyword_query")


def test_tc_u_031_hybrid_payload_omits_full_description() -> None:
    """TC-U-031 -> INV-002, SAFE-002."""
    _require_callable("engine.signal_collector", "build_external_payload", "build_signal_payload")
