from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Card(BaseModel):
    """Structure for a validation evidence card."""

    type: str
    title: str
    summary: str
    score: int = Field(ge=0, le=100)
    details: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class InterviewKit(BaseModel):
    """Actionable toolkit for user interviews."""

    script: list[dict[str, str]] = Field(
        default_factory=list, description="Questions and rationale"
    )
    outreach_templates: dict[str, str] = Field(
        default_factory=dict, description="Platform-specific drafts"
    )
    response_tracker: list[str] = Field(
        default_factory=list, description="Suggested tracking columns"
    )


class ExperimentKit(BaseModel):
    """Blueprint for a behavioral experiment (Smoke Test)."""

    hypothesis: str
    method: str
    landing_page_copy: dict[str, str] = Field(default_factory=dict)
    success_metric: str
    tool_stack: list[str] = Field(default_factory=list)


class Report(BaseModel):
    """Container for all validation cards and signals for a run."""

    run_id: UUID
    cards: list[Card]
    artifact_path: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    battle_results: dict[str, Any] | None = None
    interview_kit: InterviewKit | None = None
    experiment_kit: ExperimentKit | None = None
