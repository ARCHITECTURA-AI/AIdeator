"""SQLite-backed runs repository."""

from __future__ import annotations

import logging
from uuid import UUID

from db.base import db_session, initialize_db
from db.schema import IdeaModel, RunModel
from models.run import Run, RunStatus

LOGGER = logging.getLogger("db.runs")


def initialize():
    initialize_db()


def _to_model(run: Run) -> RunModel:
    return RunModel(
        run_id=str(run.run_id),
        idea_id=str(run.idea_id),
        tier=run.tier,
        mode=run.mode,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        duration_ms=run.duration_ms,
        error_code=run.error_code,
    )


def _from_model(model: RunModel) -> Run:
    run = Run(
        idea_id=UUID(model.idea_id),
        tier=model.tier,  # type: ignore[arg-type]
        mode=model.mode,  # type: ignore[arg-type]
    )
    run.run_id = UUID(model.run_id)
    run.status = model.status  # type: ignore[assignment]
    run.created_at = model.created_at
    run.updated_at = model.updated_at
    run.duration_ms = model.duration_ms
    run.error_code = model.error_code
    return run


def save_run(run: Run) -> Run:
    session = db_session()
    try:
        model = session.query(RunModel).filter_by(run_id=str(run.run_id)).first()
        if model:
            model.status = run.status
            model.updated_at = run.updated_at
            model.duration_ms = run.duration_ms
            model.error_code = run.error_code
        else:
            model = _to_model(run)
            session.add(model)
        session.commit()
        return run
    except Exception as e:
        session.rollback()
        LOGGER.error(f"Failed to save run: {e}")
        raise e
    finally:
        db_session.remove()


def get_run(run_id: UUID) -> Run | None:
    session = db_session()
    try:
        model = session.query(RunModel).filter_by(run_id=str(run_id)).first()
        return _from_model(model) if model else None
    finally:
        db_session.remove()


def list_runs(user_id: UUID | None = None) -> list[Run]:
    session = db_session()
    try:
        query = session.query(RunModel)
        if user_id:
            query = query.join(IdeaModel).filter(IdeaModel.user_id == str(user_id))
        models = query.order_by(RunModel.created_at.desc()).all()
        return [_from_model(m) for m in models]
    finally:
        db_session.remove()


def list_runs_for_idea(idea_id: UUID) -> list[Run]:
    session = db_session()
    try:
        models = (
            session.query(RunModel)
            .filter_by(idea_id=str(idea_id))
            .order_by(RunModel.created_at.desc())
            .all()
        )
        return [_from_model(m) for m in models]
    finally:
        db_session.remove()


def get_or_create_idempotent_run(
    *,
    idea_id: UUID,
    tier: str,
    mode: str,
    idempotency_key: str,
) -> tuple[Run, bool]:
    session = db_session()
    try:
        model = (
            session.query(RunModel)
            .filter_by(idea_id=str(idea_id), idempotency_key=idempotency_key)
            .first()
        )
        if model:
            return _from_model(model), True

        run = Run(idea_id=idea_id, tier=tier, mode=mode)  # type: ignore[arg-type]
        model = _to_model(run)
        model.idempotency_key = idempotency_key
        session.add(model)
        session.commit()
        return run, False
    except Exception as e:
        session.rollback()
        LOGGER.error(f"Failed in idempotency lookup: {e}")
        raise e
    finally:
        db_session.remove()


def transition_run(run_id: UUID, next_status: RunStatus, *, error_code: str | None = None) -> Run:
    run = get_run(run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")
    run.transition_to(next_status, error_code=error_code)
    save_run(run)
    return run


# Legacy snapshot functions for compatibility
def export_runs_snapshot():
    return {}


def import_runs_snapshot(snapshot):
    pass


# initialize() - REMOVED
