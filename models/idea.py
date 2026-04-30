"""Idea model for API and repository flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class ValidationStatus(str, Enum):
    DESK_RESEARCH = "desk_research"
    INTERVIEW_READY = "interview_ready"
    EXPERIMENT_READY = "experiment_ready"
    VALIDATED = "validated"
    PIVOT_RECOMMENDED = "pivot_recommended"


@dataclass(slots=True)
class Idea:
    title: str
    description: str
    target_user: str
    context: str
    idea_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tier: str = "Bronze"
    brand_hex: str = "#888888"
    status: ValidationStatus = ValidationStatus.DESK_RESEARCH
    workspace_id: UUID | None = None
