"""In-memory reports repository."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Final
from uuid import UUID

from models.report import Report

_REPORTS: Final[dict[UUID, Report]] = {}
LOGGER = logging.getLogger("db.reports")


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


def import_reports_snapshot(rows: Iterable[dict[str, object]]) -> None:
    _REPORTS.clear()
    for row in rows:
        cards_obj = row.get("cards")
        if not isinstance(cards_obj, list):
            continue
        LOGGER.debug(
            "import row cards runtime type",
            extra={
                "event": "import_reports_snapshot",
                "extra_fields": {"has_cards": True, "cards_type": type(cards_obj).__name__},
            },
        )
        report = Report(
            run_id=UUID(str(row["run_id"])),
            cards=cards_obj,
            artifact_path=str(row["artifact_path"]),
        )
        _REPORTS[report.run_id] = report
