"""PH-D quality/eval red-baseline tests (TC-Q-300+)."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_phd_quality", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_q_300_demand_card_semantic_eval_threshold() -> None:
    """TC-Q-300 -> COV-001, FR-005, FR-006."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phd/eval-demand")
    assert response.status_code == 200, response.text


def test_tc_q_301_competition_card_semantic_eval_threshold() -> None:
    """TC-Q-301 -> COV-001, FR-005."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phd/eval-competition")
    assert response.status_code == 200, response.text


def test_tc_q_302_cursor_notes_actionability_eval_threshold() -> None:
    """TC-Q-302 -> NO-011."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/phd/eval-cursor-notes")
    assert response.status_code == 200, response.text
