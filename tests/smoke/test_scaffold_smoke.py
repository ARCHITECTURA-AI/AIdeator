from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_healthz_smoke() -> None:
    client = TestClient(app)
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
