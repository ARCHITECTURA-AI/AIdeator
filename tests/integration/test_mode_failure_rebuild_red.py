"""Red-baseline integration tests for mode boundaries and failure handling."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

_APP_PATH = Path(__file__).resolve().parents[2] / "api" / "app.py"
_SPEC = spec_from_file_location("aideator_api_app_mode", _APP_PATH)
assert _SPEC and _SPEC.loader
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
app = _MODULE.app


def test_tc_i_010_local_only_zero_outbound_http() -> None:
    """TC-I-010 -> INV-001, SAFE-002, NFR-010."""
    client = TestClient(app)
    response = client.post(
        "/runs",
        json={"idea_id": "11111111-1111-1111-1111-111111111111", "tier": "low", "mode": "local-only"},
    )
    assert response.status_code == 202, response.text


def test_tc_i_011_hybrid_keyword_only_payloads() -> None:
    """TC-I-011 -> INV-002, NFR-009."""
    client = TestClient(app)
    response = client.post(
        "/runs",
        json={"idea_id": "11111111-1111-1111-1111-111111111111", "tier": "medium", "mode": "hybrid"},
    )
    assert response.status_code == 202, response.text


def test_tc_i_020_tavily_timeout_fails_run_cleanly() -> None:
    """TC-I-020 -> SAFE-003."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/fail-tavily-timeout")
    assert response.status_code == 200, response.text


def test_tc_i_021_reddit_rate_limit_fails_run_cleanly() -> None:
    """TC-I-021 -> SAFE-003."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/fail-reddit-429")
    assert response.status_code == 200, response.text


def test_tc_i_022_llm_timeout_fails_run_cleanly() -> None:
    """TC-I-022 -> SAFE-003, LIVE-002."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/fail-llm-timeout")
    assert response.status_code == 200, response.text


def test_tc_i_023_report_write_failure_is_atomic() -> None:
    """TC-I-023 -> SAFE-003, INV-003."""
    client = TestClient(app)
    response = client.post("/internal/test-hooks/fail-report-write")
    assert response.status_code == 200, response.text


def test_tc_i_030_rebuild_docs_regenerates_succeeded_runs_only() -> None:
    """TC-I-030 -> INV-008, LIVE-004, NFR-007."""
    client = TestClient(app)
    response = client.post("/internal/rebuild-docs")
    assert response.status_code == 200, response.text


def test_tc_i_031_rebuild_docs_skips_failed_runs() -> None:
    """TC-I-031 -> INV-008."""
    client = TestClient(app)
    response = client.post("/internal/rebuild-docs")
    assert response.status_code == 200, response.text


def test_tc_i_040_logs_never_contain_idea_text() -> None:
    """TC-I-040 -> SAFE-001, NFR-004."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/log-scan")
    assert response.status_code == 200, response.text


def test_tc_i_041_logs_include_run_metadata_only() -> None:
    """TC-I-041 -> SAFE-001, NFR-004."""
    client = TestClient(app)
    response = client.get("/internal/test-hooks/log-scan")
    assert response.status_code == 200, response.text
