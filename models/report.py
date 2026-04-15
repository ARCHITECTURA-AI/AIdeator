"""Report model."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Report:
    run_id: UUID
    cards: list[dict[str, object]]
    artifact_path: str
    citations: list[dict[str, object]]
