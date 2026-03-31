"""PH-C red-baseline integration tests (TC-I-200+)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phc_integration", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_i_200_multi_user_isolation_for_ideas_and_runs() -> None:
    """TC-I-200 -> PH-C FRs."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phc/multi-user-isolation")
    assert response.status_code == 200, response.text


def test_tc_i_201_backup_and_restore_roundtrip() -> None:
    """TC-I-201 -> SAFE-004."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phc/backup-restore")
    assert response.status_code == 200, response.text


def test_tc_i_202_sqlite_to_postgres_migration_preserves_invariants() -> None:
    """TC-I-202 -> INV-003, INV-005, INV-006."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phc/migration-check")
    assert response.status_code == 200, response.text
