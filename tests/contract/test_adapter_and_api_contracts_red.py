"""Red-baseline contract tests for adapters and API response contracts."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


def _require_callable(module_path: str, *names: str) -> Callable[..., Any]:
    module = importlib.import_module(module_path)
    for name in names:
        value = getattr(module, name, None)
        if callable(value):
            return value
    joined = ", ".join(names)
    raise AssertionError(f"Expected callable [{joined}] in {module_path}")


_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_contract", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_c_001_tavily_parser_tolerates_unknown_fields() -> None:
    """TC-C-001 -> FR-003."""
    _require_callable("adapters.tavily", "parse_tavily_response", "parse_results")


def test_tc_c_002_reddit_parser_tolerates_missing_optional_fields() -> None:
    """TC-C-002 -> FR-003."""
    _require_callable("adapters.reddit", "parse_reddit_response", "parse_results")


def test_tc_c_003_litellm_wrapper_uses_stable_response_shape() -> None:
    """TC-C-003 -> FR-004, FR-008."""
    _require_callable("adapters.llm", "extract_text", "parse_completion")


def test_tc_c_010_status_contract_contains_mode_and_disclosure() -> None:
    """TC-C-010 -> FR-002, NFR-009, NFR-010."""
    client = TestClient(app)
    response = client.get("/runs/11111111-1111-1111-1111-111111111111/status")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "mode" in payload
    assert "mode_disclosure" in payload


def test_tc_c_011_report_contract_contains_four_cards_and_artifact() -> None:
    """TC-C-011 -> FR-005, FR-006, FR-007."""
    client = TestClient(app)
    response = client.get("/runs/11111111-1111-1111-1111-111111111111/report")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "cards" in payload
    assert "artifact_path" in payload
