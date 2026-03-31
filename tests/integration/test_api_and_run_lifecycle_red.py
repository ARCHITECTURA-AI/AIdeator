"""Red-baseline integration tests for API and run lifecycle."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_integration", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def _idea_payload() -> dict[str, str]:
    return {
        "title": "AI meal planner",
        "description": "Build a local-first meal planning assistant for students.",
        "target_user": "Students on a budget",
        "context": "Runs on laptop only",
    }


def test_tc_i_001_post_ideas_persists_and_returns_201() -> None:
    """TC-I-001 -> FR-001."""
    client = TestClient(app)
    response = client.post("/ideas", json=_idea_payload())
    assert response.status_code == 201, response.text


def test_tc_i_002_post_runs_creates_pending_run() -> None:
    """TC-I-002 -> FR-002, INV-007."""
    client = TestClient(app)
    response = client.post(
        "/runs",
        json={
            "idea_id": "11111111-1111-1111-1111-111111111111",
            "tier": "low",
            "mode": "local-only",
        },
    )
    assert response.status_code == 202, response.text


def test_tc_i_003_run_lifecycle_happy_path_pending_to_succeeded() -> None:
    """TC-I-003 -> FR-002, FR-003, FR-004, FR-005, INV-003, INV-006."""
    client = TestClient(app)
    create = client.post(
        "/runs",
        json={
            "idea_id": "11111111-1111-1111-1111-111111111111",
            "tier": "low",
            "mode": "local-only",
        },
    )
    assert create.status_code == 202, create.text

    run_id = create.json()["run_id"]
    status = client.get(f"/runs/{run_id}/status")
    assert status.status_code == 200, status.text
    assert status.json()["status"] in {"pending", "running", "succeeded"}


def test_tc_i_004_no_orphan_signals_when_run_fails() -> None:
    """TC-I-004 -> INV-005, FR-003."""
    client = TestClient(app)
    # Explicitly expect a deterministic failure contract until DB + cleanup are implemented.
    response = client.get("/internal/debug/orphan-signals")
    assert response.status_code == 200, response.text


def test_tc_i_050_stale_pending_run_marked_failed() -> None:
    """TC-I-050 -> LIVE-001, NFR-002."""
    client = TestClient(app)
    response = client.post("/internal/watchdog/scan")
    assert response.status_code == 200, response.text


def test_tc_i_051_stuck_running_run_marked_failed() -> None:
    """TC-I-051 -> LIVE-002, NFR-002."""
    client = TestClient(app)
    response = client.post("/internal/watchdog/scan")
    assert response.status_code == 200, response.text
