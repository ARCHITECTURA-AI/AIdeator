"""Red-baseline end-to-end tests for critical user flows."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_e2e", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def _idea_payload() -> dict[str, str]:
    return {
        "title": "Auto budget planner",
        "description": "Generate monthly budget from bank statements locally.",
        "target_user": "Freelancers",
        "context": "privacy first",
    }


def test_tc_e2e_001_happy_path_idea_to_report() -> None:
    """TC-E2E-001 -> FR-001..FR-006, LIVE-003."""
    client = TestClient(app)
    create_idea = client.post("/ideas", json=_idea_payload())
    assert create_idea.status_code == 201, create_idea.text

    idea_id = create_idea.json()["idea_id"]
    create_run = client.post("/runs", json={"idea_id": idea_id, "tier": "low", "mode": "local-only"})
    assert create_run.status_code == 202, create_run.text

    run_id = create_run.json()["run_id"]
    report = client.get(f"/runs/{run_id}/report")
    assert report.status_code == 200, report.text


def test_tc_e2e_002_local_only_flow_never_networks_outbound() -> None:
    """TC-E2E-002 -> INV-001, SAFE-002, NFR-010, LIVE-003."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/assert-no-external-http")
    assert response.status_code == 200, response.text


def test_tc_e2e_003_deep_markdown_artifact_exists() -> None:
    """TC-E2E-003 -> FR-007, INV-008, LIVE-004."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/artifact-check")
    assert response.status_code == 200, response.text


def test_tc_e2e_004_dependency_failure_surfaces_cleanly() -> None:
    """TC-E2E-004 -> SAFE-003, FR-002, LIVE-001."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/fail-tavily-timeout")
    assert response.status_code == 200, response.text
