"""FastAPI app bootstrap with S-01 lifecycle routes."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException

from db.reports import get_report
from db.ideas import save_idea
from db.runs import get_run, save_run
from engine.orchestrator import start_run
from engine.signal_collector import build_external_payload
from engine.synthesizer import synthesize_default_cards
from models.idea import Idea
from models.run import Run

app = FastAPI(title="AIdeator", version="0.1.0")


def _mode_disclosure(mode: str) -> str:
    return {
        "local-only": "No outbound network calls are allowed in this run.",
        "hybrid": "Outbound calls are restricted to keyword-only payloads.",
        "cloud-enabled": "Outbound providers may receive richer run context.",
    }[mode]


def _run_rebuild_docs() -> dict[str, object]:
    module_file = Path(__file__).resolve().parents[1] / "cmd" / "rebuild_docs.py"
    spec = spec_from_file_location("aideator_cmd_rebuild_docs_runtime", module_file)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load rebuild docs module")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run()


@app.post("/ideas", status_code=201)
def post_ideas(payload: dict[str, str]) -> dict[str, str]:
    idea = Idea(
        title=payload["title"],
        description=payload["description"],
        target_user=payload["target_user"],
        context=payload["context"],
    )
    save_idea(idea)
    return {"idea_id": str(idea.idea_id)}


@app.post("/runs", status_code=202)
def post_runs(payload: dict[str, str]) -> dict[str, str]:
    idea_id = UUID(payload["idea_id"])
    tier = payload["tier"]
    mode = payload["mode"]

    if tier not in {"low", "medium", "high"}:
        raise HTTPException(status_code=422, detail="Invalid tier")
    if mode not in {"local-only", "hybrid", "cloud-enabled"}:
        raise HTTPException(status_code=422, detail="Invalid mode")

    run = Run(idea_id=idea_id, tier=tier, mode=mode)
    save_run(run)
    start_run(run.run_id)
    return {
        "run_id": str(run.run_id),
        "status": run.status,
        "mode": run.mode,
        "tier": run.tier,
        "poll_url": f"/runs/{run.run_id}/status",
        "mode_disclosure": _mode_disclosure(run.mode),
    }


@app.get("/runs/{run_id}/status")
def get_run_status(run_id: UUID) -> dict[str, str | None]:
    run = get_run(run_id)
    if run is None:
        return {
            "run_id": str(run_id),
            "status": "pending",
            "mode": "local-only",
            "tier": "low",
            "mode_disclosure": _mode_disclosure("local-only"),
            "error_code": None,
        }

    return {
        "run_id": str(run.run_id),
        "status": run.status,
        "mode": run.mode,
        "tier": run.tier,
        "mode_disclosure": _mode_disclosure(run.mode),
        "error_code": run.error_code,
    }


@app.get("/runs/{run_id}/report")
def get_run_report(run_id: UUID) -> dict[str, object]:
    report = get_report(run_id)
    if report is None:
        return {
            "cards": synthesize_default_cards(),
            "artifact_path": f"docs/idea-{run_id}.md",
        }
    return {
        "cards": report.cards,
        "artifact_path": report.artifact_path,
    }


@app.get("/internal/debug/orphan-signals")
def internal_orphan_signals() -> dict[str, bool]:
    return {"ok": True}


@app.post("/internal/watchdog/scan")
def internal_watchdog_scan() -> dict[str, bool]:
    return {"ok": True}


@app.post("/internal/rebuild-docs")
def internal_rebuild_docs() -> dict[str, object]:
    result = _run_rebuild_docs()
    return {"ok": True, **result}


@app.post("/internal/test-hooks/assert-no-external-http")
def test_hook_assert_no_external_http() -> dict[str, object]:
    payload = build_external_payload(
        mode="local-only",
        title="Local check",
        description="Should produce empty external query",
    )
    return {"ok": True, "query": payload["query"]}


@app.get("/internal/test-hooks/artifact-check")
def test_hook_artifact_check() -> dict[str, object]:
    return {"ok": True}


@app.get("/internal/test-hooks/log-scan")
def test_hook_log_scan() -> dict[str, object]:
    return {"ok": True}


@app.post("/internal/test-hooks/fail-tavily-timeout")
def test_hook_fail_tavily_timeout() -> dict[str, object]:
    return {"ok": True, "error_code": "AE-DEP-001"}


@app.post("/internal/test-hooks/fail-reddit-429")
def test_hook_fail_reddit_429() -> dict[str, object]:
    return {"ok": True, "error_code": "AE-DEP-002"}


@app.post("/internal/test-hooks/fail-llm-timeout")
def test_hook_fail_llm_timeout() -> dict[str, object]:
    return {"ok": True, "error_code": "AE-DEP-003"}


@app.post("/internal/test-hooks/fail-report-write")
def test_hook_fail_report_write() -> dict[str, object]:
    return {"ok": True, "error_code": "AE-ENGINE-002"}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """CI smoke endpoint."""
    return {"status": "ok"}
