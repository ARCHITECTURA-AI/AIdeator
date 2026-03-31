"""PH-D red-baseline end-to-end tests (TC-E2E-300)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phd_e2e", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_e2e_300_cross_version_export_import_roundtrip() -> None:
    """TC-E2E-300 -> NO-005."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phd/e2e-export-import")
    assert response.status_code == 200, response.text
