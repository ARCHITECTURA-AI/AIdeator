"""PH-B red-baseline contract tests (TC-C-100+)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phb_contract", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_c_100_report_contract_backward_compatible_with_optional_fields() -> None:
    """TC-C-100 -> FR-005."""
    client = TestClient(app)
    response = client.get("/runs/11111111-1111-1111-1111-111111111111/report")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "run_id" in payload
    assert "cards" in payload


def test_tc_c_101_error_response_schema_stable() -> None:
    """TC-C-101 -> SAFE-003."""
    client = TestClient(app)
    response = client.get("/runs/not-a-real-id/status")
    assert response.status_code in {400, 404}, response.text
    payload = response.json()
    assert "error_code" in payload
    assert "message" in payload


def test_tc_c_110_tavily_contract_drift_tolerated() -> None:
    """TC-C-110 -> FR-003."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phb/contract-tavily-drift")
    assert response.status_code == 200, response.text


def test_tc_c_111_reddit_contract_drift_tolerated() -> None:
    """TC-C-111 -> FR-003."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phb/contract-reddit-drift")
    assert response.status_code == 200, response.text
