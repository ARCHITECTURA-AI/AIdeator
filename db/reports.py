"""In-memory reports repository."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Final
from uuid import UUID

from db.base import BaseJsonStorage
from models.report import Report

_STORAGE_PATH: Final[Path] = Path("data/reports.json")
_REPORTS: Final[dict[UUID, Report]] = {}
_STORAGE = BaseJsonStorage(_STORAGE_PATH, "db.reports")
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
    return [
        {
            "run_id": str(report.run_id),
            "cards": report.cards,
            "artifact_path": report.artifact_path,
            "citations": report.citations,
        }
        for report in _REPORTS.values()
    ]


def import_reports_snapshot(rows: object) -> None:
    if not isinstance(rows, list):
        return
    _REPORTS.clear()
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            report = Report(
                run_id=UUID(str(row["run_id"])),
                cards=row["cards"],  # type: ignore[arg-type]
                artifact_path=str(row["artifact_path"]),
                citations=row.get("citations", []),  # type: ignore[arg-type]
            )
            _REPORTS[report.run_id] = report
        except (KeyError, ValueError) as e:
            LOGGER.error(f"Failed to import report row: {e}")


# Auto-initialize on import
initialize()
