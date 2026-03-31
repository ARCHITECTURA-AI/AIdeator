"""In-memory runs repository (S-01 persistence skeleton)."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from models.run import Run, RunStatus

_RUNS: Final[dict[UUID, Run]] = {}
_RUN_HISTORY: Final[dict[UUID, list[UUID]]] = {}
_IDEMPOTENCY_INDEX: Final[dict[tuple[UUID, str], UUID]] = {}


def save_run(run: Run) -> Run:
    _RUNS[run.run_id] = run
    _RUN_HISTORY.setdefault(run.idea_id, []).append(run.run_id)
    return run


def get_run(run_id: UUID) -> Run | None:
    return _RUNS.get(run_id)


def list_runs() -> list[Run]:
    return list(_RUNS.values())


def list_runs_for_idea(idea_id: UUID) -> list[Run]:
    run_ids = _RUN_HISTORY.get(idea_id, [])
    return [run for run_id in run_ids if (run := _RUNS.get(run_id)) is not None]


def get_or_create_idempotent_run(
    *,
    idea_id: UUID,
    tier: str,
    mode: str,
    idempotency_key: str,
) -> tuple[Run, bool]:
    existing_run_id = _IDEMPOTENCY_INDEX.get((idea_id, idempotency_key))
    if existing_run_id is not None:
        run = _RUNS[existing_run_id]
        return run, True

    run = Run(idea_id=idea_id, tier=tier, mode=mode)
    save_run(run)
    _IDEMPOTENCY_INDEX[(idea_id, idempotency_key)] = run.run_id
    return run, False


def transition_run(run_id: UUID, next_status: RunStatus, *, error_code: str | None = None) -> Run:
    run = _RUNS[run_id]
    run.transition_to(next_status, error_code=error_code)
    return run
