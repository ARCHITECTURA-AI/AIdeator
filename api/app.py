"""FastAPI app bootstrap with S-01 lifecycle routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import FastAPI, HTTPException

from db.ideas import save_idea
from db.runs import get_run, save_run
from engine.orchestrator import start_run
from models.idea import Idea
from models.run import Run

app = FastAPI(title="AIdeator", version="0.1.0")


def _mode_disclosure(mode: str) -> str:
    return {
        "local-only": "No outbound network calls are allowed in this run.",
        "hybrid": "Outbound calls are restricted to keyword-only payloads.",
        "cloud-enabled": "Outbound providers may receive richer run context.",
    }[mode]


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
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": str(run.run_id),
        "status": run.status,
        "mode": run.mode,
        "tier": run.tier,
        "mode_disclosure": _mode_disclosure(run.mode),
        "error_code": run.error_code,
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """CI smoke endpoint."""
    return {"status": "ok"}
