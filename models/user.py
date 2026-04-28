"""User domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(slots=True)
class User:
    email: str
    hashed_password: str
    user_id: UUID = field(default_factory=uuid4)
    full_name: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
