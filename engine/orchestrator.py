"""Thin S-01 orchestrator for lifecycle progression."""

from __future__ import annotations

from uuid import UUID

from db.runs import transition_run


def start_run(run_id: UUID) -> None:
    """Advance a run through the minimal happy-path lifecycle."""
    transition_run(run_id, "running")
    transition_run(run_id, "succeeded")
