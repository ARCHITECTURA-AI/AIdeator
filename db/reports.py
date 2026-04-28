"""SQLite-backed reports repository."""

from __future__ import annotations

import logging
from uuid import UUID

from db.base import db_session, initialize_db
from db.schema import ReportModel
from models.report import Report

LOGGER = logging.getLogger("db.reports")


def initialize():
    initialize_db()


def _to_model(report: Report) -> ReportModel:
    return ReportModel(
        run_id=str(report.run_id),
        cards=[card.model_dump() for card in report.cards],
        artifact_path=report.artifact_path,
        citations=report.citations,
        battle_results=report.battle_results,
    )


def save_report(report: Report) -> Report:
    session = db_session()
    try:
        model = session.query(ReportModel).filter_by(run_id=str(report.run_id)).first()
        if model:
            model.cards = [card.model_dump() for card in report.cards]
            model.artifact_path = report.artifact_path
            model.citations = report.citations
            model.battle_results = report.battle_results
        else:
            model = _to_model(report)
            session.add(model)
        session.commit()
        return report
    except Exception as e:
        session.rollback()
        LOGGER.error(f"Failed to save report: {e}")
        raise e
    finally:
        db_session.remove()


def get_report(run_id: UUID) -> Report | None:
    session = db_session()
    try:
        model = session.query(ReportModel).filter_by(run_id=str(run_id)).first()
        if not model:
            return None
        return Report(
            run_id=UUID(model.run_id),
            cards=model.cards,
            artifact_path=model.artifact_path,
            citations=model.citations,
            battle_results=model.battle_results,
        )
    finally:
        db_session.remove()


def list_reports() -> list[Report]:
    session = db_session()
    try:
        models = session.query(ReportModel).all()
        return [
            Report(
                run_id=UUID(m.run_id),
                cards=m.cards,
                artifact_path=m.artifact_path,
                citations=m.citations,
                battle_results=m.battle_results,
            )
            for m in models
        ]
    finally:
        db_session.remove()


# Legacy snapshot functions
def export_reports_snapshot():
    return []


def import_reports_snapshot(rows):
    pass


initialize()
