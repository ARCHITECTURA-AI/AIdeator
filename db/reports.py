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


def export_reports_snapshot() -> list[dict[str, object]]:
    return [
        {
            "run_id": str(report.run_id),
            "cards": report.cards,
            "artifact_path": report.artifact_path,
        }
        for report in _REPORTS.values()
    ]


def import_reports_snapshot(rows: list[dict[str, object]]) -> None:
    _REPORTS.clear()
    for row in rows:
        report = Report(
            run_id=UUID(str(row["run_id"])),
            cards=list(row["cards"]),  # type: ignore[arg-type]
            artifact_path=str(row["artifact_path"]),
        )
        _REPORTS[report.run_id] = report
