"""Runs API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.runs import get_run, save_run
from engine.orchestrator import start_run
from models.run import Run, RunMode, RunTier

router = APIRouter(tags=["runs"])


class CreateRunRequest(BaseModel):
    idea_id: UUID
    tier: RunTier
    mode: RunMode


class CreateRunResponse(BaseModel):
    run_id: str
    status: str
    mode: str
    tier: str
    poll_url: str
    mode_disclosure: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    mode: str
    tier: str
    mode_disclosure: str
    error_code: str | None = None


def _mode_disclosure(mode: str) -> str:
    return {
        "local-only": "No outbound network calls are allowed in this run.",
        "hybrid": "Outbound calls are restricted to keyword-only payloads.",
        "cloud-enabled": "Outbound providers may receive richer run context.",
    }[mode]


@router.post("/runs", status_code=202, response_model=CreateRunResponse)
def post_runs(payload: CreateRunRequest) -> CreateRunResponse:
    run = Run(idea_id=payload.idea_id, tier=payload.tier, mode=payload.mode)
    save_run(run)
    start_run(run.run_id)
    return CreateRunResponse(
        run_id=str(run.run_id),
        status=run.status,
        mode=run.mode,
        tier=run.tier,
        poll_url=f"/runs/{run.run_id}/status",
        mode_disclosure=_mode_disclosure(run.mode),
    )


@router.get("/runs/{run_id}/status", response_model=RunStatusResponse)
def get_run_status(run_id: UUID) -> RunStatusResponse:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunStatusResponse(
        run_id=str(run.run_id),
        status=run.status,
        mode=run.mode,
        tier=run.tier,
        mode_disclosure=_mode_disclosure(run.mode),
        error_code=run.error_code,
    )
