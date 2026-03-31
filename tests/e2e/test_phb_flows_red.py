"""PH-B red-baseline end-to-end tests (TC-E2E-100+)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phb_e2e", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_e2e_100_multi_run_history_flow() -> None:
    """TC-E2E-100 -> FR-001, FR-002."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/phb/e2e-multi-run-history")
    assert response.status_code == 200, response.text


def test_tc_e2e_101_tier_upgrade_flow_low_to_medium() -> None:
    """TC-E2E-101 -> FR-002."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/phb/e2e-tier-upgrade")
    assert response.status_code == 200, response.text


def test_tc_e2e_102_error_recovery_flow_failed_then_succeeded() -> None:
    """TC-E2E-102 -> SAFE-003, FR-002."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/phb/e2e-error-recovery")
    assert response.status_code == 200, response.text
