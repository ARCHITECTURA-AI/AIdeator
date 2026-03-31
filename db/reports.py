"""In-memory reports repository."""

from __future__ import annotations

import json
import time
from collections.abc import Iterable
from typing import Final
from uuid import UUID

from models.report import Report

_REPORTS: Final[dict[UUID, Report]] = {}


def _debug_log(
    *,
    run_id: str,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, object],
) -> None:
    # region agent log
    with open("debug-8daad7.log", "a", encoding="utf-8") as debug_file:
        debug_file.write(
            json.dumps(
                {
                    "sessionId": "8daad7",
                    "runId": run_id,
                    "hypothesisId": hypothesis_id,
                    "location": location,
                    "message": message,
                    "data": data,
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )
    # endregion


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
        _debug_log(
            run_id="pre-fix",
            hypothesis_id="H1",
            location="db/reports.py:import_reports_snapshot",
            message="import row cards runtime type",
            data={"has_cards": True, "cards_type": type(cards_obj).__name__},
        )
        report = Report(
            run_id=UUID(str(row["run_id"])),
            cards=cards_obj,
            artifact_path=str(row["artifact_path"]),
        )
        _REPORTS[report.run_id] = report
