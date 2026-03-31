"""PH-C red-baseline end-to-end tests (TC-E2E-200)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phc_e2e", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_e2e_200_zero_downtime_upgrade_from_a_to_c() -> None:
    """TC-E2E-200 -> PH-C FRs."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/phc/e2e-upgrade")
    assert response.status_code == 200, response.text
