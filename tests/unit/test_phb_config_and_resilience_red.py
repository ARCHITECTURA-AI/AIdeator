"""PH-B red-baseline unit tests (TC-U-100+)."""

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


def test_tc_u_100_model_routing_yaml_validation() -> None:
    """TC-U-100 -> FR-008, ADR-006."""
    _require_callable("config.model_routing", "load_routing_config", "validate_model_routing")


def test_tc_u_101_routing_rejects_unknown_mode_or_tier() -> None:
    """TC-U-101 -> FR-008."""
    _require_callable("config.model_routing", "resolve_route", "get_route_for_mode_tier")


def test_tc_u_102_prompt_registry_requires_prompt_files() -> None:
    """TC-U-102 -> FR-008."""
    _require_callable("config.model_routing", "validate_prompt_registry", "load_prompt_registry")


def test_tc_u_110_artifact_contains_cursor_claude_usage_notes() -> None:
    """TC-U-110 -> FR-007, COV-003."""
    _require_callable("engine.synthesizer", "build_markdown_artifact", "render_markdown_report")


def test_tc_u_120_modeguard_handles_malformed_hosts_safely() -> None:
    """TC-U-120 -> INV-001, SAFE-002."""
    _require_callable("engine.mode_guard", "check", "is_allowed_destination")


def test_tc_u_121_log_sanitizer_robust_to_arbitrary_shapes() -> None:
    """TC-U-121 -> SAFE-001, NFR-004."""
    _require_callable("infra.logging", "sanitize_log_event", "redact_log_payload")
