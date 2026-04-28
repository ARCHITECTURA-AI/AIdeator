"""SQLite-backed signals repository."""

from __future__ import annotations

import logging
from uuid import UUID

from db.base import db_session, initialize_db
from db.schema import SignalModel

LOGGER = logging.getLogger("db.signals")


def initialize():
    initialize_db()


def save_signal(run_id: UUID, signal: dict[str, str]) -> None:
    session = db_session()
    try:
        model = SignalModel(run_id=str(run_id), data=signal)
        session.add(model)
        session.commit()
    except Exception as e:
        session.rollback()
        LOGGER.error(f"Failed to save signal: {e}")
        raise e
    finally:
        db_session.remove()


def list_signals(run_id: UUID) -> list[dict[str, str]]:
    session = db_session()
    try:
        models = session.query(SignalModel).filter_by(run_id=str(run_id)).all()
        return [m.data for m in models]
    finally:
        db_session.remove()


# Legacy snapshot functions
def export_signals_snapshot():
    return {}


def import_signals_snapshot(snapshot):
    pass


# initialize() - REMOVED
