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


class Report(BaseModel):
    """Container for all validation cards and signals for a run."""

    run_id: UUID
    cards: list[Card]
    artifact_path: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
