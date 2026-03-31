"""Idea model for API and repository flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(slots=True)
class Idea:
    title: str
    description: str
    target_user: str
    context: str
    idea_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
