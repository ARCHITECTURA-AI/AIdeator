"""In-memory ideas repository (S-01 persistence skeleton)."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from models.idea import Idea

_IDEAS: Final[dict[UUID, Idea]] = {}


def save_idea(idea: Idea) -> Idea:
    _IDEAS[idea.idea_id] = idea
    return idea


def get_idea(idea_id: UUID) -> Idea | None:
    return _IDEAS.get(idea_id)
