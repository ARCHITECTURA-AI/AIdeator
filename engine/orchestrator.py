"""Thin S-01 orchestrator for lifecycle progression."""

from __future__ import annotations

from uuid import UUID

from db.reports import save_report
from db.runs import get_run
from db.runs import transition_run
from engine.synthesizer import synthesize_default_cards
from models.report import Report


def start_run(run_id: UUID) -> None:
    """Advance a run through the minimal happy-path lifecycle."""
    transition_run(run_id, "running")
    run = get_run(run_id)
    if run is None:
        raise ValueError("Run not found")
    cards = synthesize_default_cards()
    save_report(Report(run_id=run_id, cards=cards, artifact_path=f"docs/idea-{run.idea_id}.md"))
    transition_run(run_id, "succeeded")
