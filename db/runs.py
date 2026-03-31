"""In-memory runs repository (S-01 persistence skeleton)."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from models.run import Run, RunStatus

_RUNS: Final[dict[UUID, Run]] = {}


def save_run(run: Run) -> Run:
    _RUNS[run.run_id] = run
    return run


def get_run(run_id: UUID) -> Run | None:
    return _RUNS.get(run_id)


def transition_run(run_id: UUID, next_status: RunStatus, *, error_code: str | None = None) -> Run:
    run = _RUNS[run_id]
    run.transition_to(next_status, error_code=error_code)
    return run
