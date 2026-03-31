"""In-memory ideas repository (S-01 persistence skeleton)."""

from __future__ import annotations

from datetime import datetime
from typing import Final
from uuid import UUID

from models.idea import Idea

_IDEAS: Final[dict[UUID, Idea]] = {}


def save_idea(idea: Idea) -> Idea:
    _IDEAS[idea.idea_id] = idea
    return idea


def get_idea(idea_id: UUID) -> Idea | None:
    return _IDEAS.get(idea_id)


def list_ideas() -> list[Idea]:
    return list(_IDEAS.values())


def export_ideas_snapshot() -> list[dict[str, str]]:
    return [
        {
            "idea_id": str(idea.idea_id),
            "title": idea.title,
            "description": idea.description,
            "target_user": idea.target_user,
            "context": idea.context,
            "created_at": idea.created_at.isoformat(),
        }
        for idea in _IDEAS.values()
    ]


def import_ideas_snapshot(rows: list[dict[str, str]]) -> None:
    _IDEAS.clear()
    for row in rows:
        idea = Idea(
            title=row["title"],
            description=row["description"],
            target_user=row["target_user"],
            context=row["context"],
        )
        idea.idea_id = UUID(row["idea_id"])
        idea.created_at = datetime.fromisoformat(row["created_at"])
        _IDEAS[idea.idea_id] = idea
