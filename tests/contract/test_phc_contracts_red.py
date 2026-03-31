"""PH-C red-baseline contract tests (TC-C-200)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phc_contract", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_c_200_backwards_compatible_api_minor_version_contract() -> None:
    """TC-C-200 -> PH-C FRs."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/phc/contract-backcompat")
    assert response.status_code == 200, response.text
