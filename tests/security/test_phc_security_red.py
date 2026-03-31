"""PH-C red-baseline security tests (TC-S-200+)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phc_security", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_s_200_no_secrets_in_container_logs_or_crash_dumps() -> None:
    """TC-S-200 -> SAFE-001."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phc/security-log-secret-scan")
    assert response.status_code == 200, response.text


def test_tc_s_201_default_network_bind_is_localhost() -> None:
    """TC-S-201 -> SAFE-002."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/phc/security-bind-check")
    assert response.status_code == 200, response.text
