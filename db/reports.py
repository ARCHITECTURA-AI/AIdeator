"""In-memory reports repository."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final
from uuid import UUID

from db.base import BaseJsonStorage
from models.report import Report

_STORAGE_PATH: Final[Path] = Path("data/reports.json")
_REPORTS: Final[dict[UUID, Report]] = {}
_STORAGE: BaseJsonStorage[dict[str, object]] = BaseJsonStorage(_STORAGE_PATH, "db.reports")
LOGGER = logging.getLogger("db.reports")


def _flush():
    """Flush reports to disk."""
    _STORAGE.flush(export_reports_snapshot)


def initialize():
    """Load reports from disk."""
    _STORAGE.load(import_reports_snapshot)


def save_report(report: Report) -> Report:
    _REPORTS[report.run_id] = report
    _flush()
    return report


def get_report(run_id: UUID) -> Report | None:
    return _REPORTS.get(run_id)


def list_reports() -> list[Report]:
    return list(_REPORTS.values())


def export_reports_snapshot() -> list[dict[str, object]]:
    return [report.model_dump(mode="json") for report in _REPORTS.values()]


def import_reports_snapshot(rows: object) -> None:
    if not isinstance(rows, list):
        return
    _REPORTS.clear()
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            report = Report.model_validate(row)
            _REPORTS[report.run_id] = report
        except Exception as e:
            LOGGER.error(f"Failed to import report row {row.get('run_id', 'unknown')}: {e}")


# Auto-initialize on import
initialize()
