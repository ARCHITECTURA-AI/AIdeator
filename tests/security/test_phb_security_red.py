"""PH-B red-baseline security tests (TC-S-100+)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phb_security", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_s_100_config_poisoning_is_blocked() -> None:
    """TC-S-100 -> SAFE-005."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phb/security-config-poisoning")
    assert response.status_code == 200, response.text


def test_tc_s_101_docs_path_traversal_prevention() -> None:
    """TC-S-101 -> INV-008, SAFE-004."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phb/security-path-traversal")
    assert response.status_code == 200, response.text


def test_tc_s_102_parallel_run_isolation_under_stress() -> None:
    """TC-S-102 -> INV-005, INV-003."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phb/security-concurrency-isolation")
    assert response.status_code == 200, response.text
