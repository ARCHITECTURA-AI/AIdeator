"""Thin S-01 orchestrator for lifecycle progression."""

from __future__ import annotations

import logging
import time
from uuid import UUID

from db.reports import save_report
from db.runs import get_run, transition_run
from engine.synthesizer import synthesize_default_cards
from models.report import Report

LOGGER = logging.getLogger("engine.orchestrator")


def start_run(run_id: UUID) -> None:
    """Advance a run through the minimal happy-path lifecycle."""
    started_at = time.perf_counter()
    transition_run(run_id, "running")
    run = get_run(run_id)
    if run is None:
        raise ValueError("Run not found")

    LOGGER.info(
        "Run started",
        extra={
            "event": "run_started",
            "extra_fields": {"run_id": str(run_id), "idea_id": str(run.idea_id), "mode": run.mode},
        },
    )

    try:
        cards = synthesize_default_cards()
        save_report(Report(run_id=run_id, cards=cards, artifact_path=f"docs/idea-{run.idea_id}.md"))
        transition_run(run_id, "succeeded")
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.info(
            "Run succeeded",
            extra={
                "event": "run_succeeded",
                "extra_fields": {
                    "run_id": str(run_id),
                    "idea_id": str(run.idea_id),
                    "mode": run.mode,
                    "duration_ms": duration_ms,
                },
            },
        )
    except Exception:
        transition_run(run_id, "failed", error_code="AE-ENGINE-001")
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        LOGGER.error(
            "Run failed",
            extra={
                "event": "run_failed",
                "extra_fields": {
                    "run_id": str(run_id),
                    "idea_id": str(run.idea_id),
                    "mode": run.mode,
                    "duration_ms": duration_ms,
                },
            },
            exc_info=True,
        )
        raise
