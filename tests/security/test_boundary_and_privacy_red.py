"""Red-baseline security tests for trust boundaries and privacy invariants."""

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
_SPEC = spec_from_file_location("aideator_api_app_security", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_s_001_modeguard_has_explicit_block_path() -> None:
    """TC-S-001 -> INV-001, SAFE-002."""
    _require_callable("engine.mode_guard", "block_external", "check")


def test_tc_s_002_local_only_zero_outbound_integration() -> None:
    """TC-S-002 -> INV-001, SAFE-002."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/assert-no-external-http")
    assert response.status_code == 200, response.text


def test_tc_s_003_logs_never_contain_user_content() -> None:
    """TC-S-003 -> SAFE-001."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/log-scan")
    assert response.status_code == 200, response.text


def test_tc_s_004_hybrid_enforcement_present() -> None:
    """TC-S-004 -> INV-002, SAFE-002."""
    _require_callable("engine.mode_guard", "enforce_hybrid_keywords", "check")


def test_tc_s_005_dependency_failures_do_not_yield_partial_success() -> None:
    """TC-S-005 -> SAFE-003."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/fail-report-write")
    assert response.status_code == 200, response.text
