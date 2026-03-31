"""PH-D red-baseline unit tests (TC-U-300+)."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any


def _require_callable(module_path: str, *names: str) -> Callable[..., Any]:
    module = importlib.import_module(module_path)
    for name in names:
        value = getattr(module, name, None)
        if callable(value):
            return value
    joined = ", ".join(names)
    raise AssertionError(f"Expected callable [{joined}] in {module_path}")


def test_tc_u_300_plugin_registration_contract_helper() -> None:
    """TC-U-300 -> SAFE-005."""
    _require_callable("engine.plugins", "register_plugin", "load_plugins")


def test_tc_u_301_plugin_sandbox_policy_helper() -> None:
    """TC-U-301 -> SAFE-005."""
    _require_callable("engine.plugin_sandbox", "enforce_plugin_policy", "assert_plugin_caps")


def test_tc_u_302_eval_budget_guard_helper() -> None:
    """TC-U-302 -> TC-P-300 support."""
    _require_callable("engine.evals", "enforce_eval_budget", "check_eval_budget")
