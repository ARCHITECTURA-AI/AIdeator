"""PH-D red-baseline contract tests (TC-C-300)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phd_contract", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_c_300_plugin_api_contract_is_stable() -> None:
    """TC-C-300 -> SAFE-005."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/phd/plugin-contract")
    assert response.status_code == 200, response.text
