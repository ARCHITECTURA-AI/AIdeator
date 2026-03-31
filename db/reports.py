"""In-memory reports repository."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from models.report import Report

_REPORTS: Final[dict[UUID, Report]] = {}


def save_report(report: Report) -> Report:
    _REPORTS[report.run_id] = report
    return report


def get_report(run_id: UUID) -> Report | None:
    return _REPORTS.get(run_id)


def list_reports() -> list[Report]:
    return list(_REPORTS.values())
