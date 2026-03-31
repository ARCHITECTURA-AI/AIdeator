"""PH-D red-baseline integration tests (TC-I-300+)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phd_integration", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_i_300_plugin_cannot_write_db_directly() -> None:
    """TC-I-300 -> SAFE-005."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phd/plugin-db-write-attempt")
    assert response.status_code == 200, response.text


def test_tc_i_301_new_signal_sources_respect_mode_boundaries() -> None:
    """TC-I-301 -> INV-001, INV-002."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phd/plugin-mode-boundary")
    assert response.status_code == 200, response.text
