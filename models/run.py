"""Run model and state-transition guardrails."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

RunStatus = Literal["pending", "running", "succeeded", "failed"]
RunTier = Literal["low", "medium", "high"]
RunMode = Literal["local-only", "hybrid", "cloud-enabled"]

_ALLOWED_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    "pending": {"running", "failed"},
    "running": {"succeeded", "failed"},
    "succeeded": set(),
    "failed": set(),
}


@dataclass(slots=True)
class Run:
    idea_id: UUID
    tier: RunTier
    mode: RunMode
    run_id: UUID = field(default_factory=uuid4)
    status: RunStatus = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_code: str | None = None

    def transition_to(self, next_status: RunStatus, *, error_code: str | None = None) -> None:
        if next_status not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(f"Invalid run transition: {self.status} -> {next_status}")

        self.status = next_status
        self.error_code = error_code
        self.updated_at = datetime.now(timezone.utc)
