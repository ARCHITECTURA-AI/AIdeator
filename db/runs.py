"""In-memory runs repository (S-01 persistence skeleton)."""

from __future__ import annotations

from datetime import datetime
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


def export_runs_snapshot() -> dict[str, object]:
    runs = [
        {
            "run_id": str(run.run_id),
            "idea_id": str(run.idea_id),
            "tier": run.tier,
            "mode": run.mode,
            "status": run.status,
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat(),
            "error_code": run.error_code,
        }
        for run in _RUNS.values()
    ]
    history = {str(idea_id): [str(run_id) for run_id in run_ids] for idea_id, run_ids in _RUN_HISTORY.items()}
    idempotency = [
        {"idea_id": str(idea_id), "key": key, "run_id": str(run_id)}
        for (idea_id, key), run_id in _IDEMPOTENCY_INDEX.items()
    ]
    return {"runs": runs, "history": history, "idempotency": idempotency}


def import_runs_snapshot(snapshot: dict[str, object]) -> None:
    _RUNS.clear()
    _RUN_HISTORY.clear()
    _IDEMPOTENCY_INDEX.clear()

    for row in snapshot.get("runs", []):
        run_data = row
        if not isinstance(run_data, dict):
            continue
        run = Run(
            idea_id=UUID(str(run_data["idea_id"])),
            tier=str(run_data["tier"]),  # type: ignore[arg-type]
            mode=str(run_data["mode"]),  # type: ignore[arg-type]
        )
        run.run_id = UUID(str(run_data["run_id"]))
        run.status = str(run_data["status"])  # type: ignore[assignment]
        run.created_at = datetime.fromisoformat(str(run_data["created_at"]))
        run.updated_at = datetime.fromisoformat(str(run_data["updated_at"]))
        error_code = run_data.get("error_code")
        run.error_code = str(error_code) if error_code is not None else None
        _RUNS[run.run_id] = run

    history = snapshot.get("history", {})
    if isinstance(history, dict):
        for idea_id, run_ids in history.items():
            if not isinstance(run_ids, list):
                continue
            _RUN_HISTORY[UUID(str(idea_id))] = [UUID(str(run_id)) for run_id in run_ids]

    idempotency = snapshot.get("idempotency", [])
    if isinstance(idempotency, list):
        for row in idempotency:
            if not isinstance(row, dict):
                continue
            _IDEMPOTENCY_INDEX[(UUID(str(row["idea_id"])), str(row["key"]))] = UUID(str(row["run_id"]))
