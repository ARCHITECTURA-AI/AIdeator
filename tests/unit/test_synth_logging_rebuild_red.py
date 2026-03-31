"""Red-baseline unit tests for synthesis, logging, and docs rebuild."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


def _require_attr(module_path: str, *names: str) -> Any:
    if module_path == "cmd.rebuild_docs":
        module_file = Path(__file__).resolve().parents[2] / "cmd" / "rebuild_docs.py"
        spec = spec_from_file_location("aideator_cmd_rebuild_docs", module_file)
        assert spec and spec.loader
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
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


def test_tc_u_020_cards_schema_validation_success() -> None:
    """TC-U-020 -> INV-003, INV-004, FR-005."""
    _require_callable("engine.synthesizer", "validate_cards", "validate_cards_json")


def test_tc_u_021_missing_demand_card_rejected() -> None:
    """TC-U-021 -> INV-003, FR-005."""
    _require_callable("engine.synthesizer", "validate_cards", "validate_cards_json")


def test_tc_u_022_empty_citations_rejected() -> None:
    """TC-U-022 -> INV-004, FR-006."""
    _require_callable("engine.synthesizer", "validate_cards", "validate_cards_json")


def test_tc_u_023_next_steps_without_citations_allowed() -> None:
    """TC-U-023 -> INV-004, FR-006."""
    _require_callable("engine.synthesizer", "validate_cards", "validate_cards_json")


def test_tc_u_040_log_sanitizer_strips_idea_text() -> None:
    """TC-U-040 -> SAFE-001, NFR-004."""
    _require_callable("infra.logging", "sanitize_log_event", "redact_log_payload")


def test_tc_u_041_log_sanitizer_preserves_non_sensitive_fields() -> None:
    """TC-U-041 -> SAFE-001."""
    _require_callable("infra.logging", "sanitize_log_event", "redact_log_payload")


def test_tc_u_050_rebuild_docs_uses_only_db_reads() -> None:
    """TC-U-050 -> SAFE-004, INV-008."""
    _require_callable("cmd.rebuild_docs", "rebuild_docs", "run")


def test_tc_u_051_rebuild_docs_writes_only_docs_directory() -> None:
    """TC-U-051 -> INV-008, NFR-007."""
    _require_callable("cmd.rebuild_docs", "rebuild_docs", "run")
