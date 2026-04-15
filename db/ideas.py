"""In-memory ideas repository (S-01 persistence skeleton)."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Final
from uuid import UUID

from db.base import BaseJsonStorage
from models.idea import Idea

_STORAGE_PATH: Final[Path] = Path("data/ideas.json")
_IDEAS: Final[dict[UUID, Idea]] = {}
_STORAGE = BaseJsonStorage(_STORAGE_PATH, "db.ideas")
LOGGER = logging.getLogger("db.ideas")


def _flush():
    """Flush ideas to disk."""
    _STORAGE.flush(export_ideas_snapshot)


def initialize():
    """Load ideas from disk."""
    _STORAGE.load(import_ideas_snapshot)


def _generate_brand_hex(text: str) -> str:
    """Generate a premium-looking brand color from text."""
    # Curated palette of premium/neon/tech colors
    PALETTE = [
        "#A7A5FF",  # Primary Indigo
        "#00F2FE",  # Cyan Tech
        "#4FACFE",  # Blue Sky
        "#7028FF",  # Deep Purple
        "#FF0080",  # Cyber Pink
        "#00FF41",  # Matrix Green
        "#F9D423",  # Sun Warning
    ]
    import hashlib
    h = int(hashlib.md5(text.encode()).hexdigest(), 16)
    return PALETTE[h % len(PALETTE)]


def save_idea(idea: Idea) -> Idea:
    if idea.brand_hex == "#888888":
        idea.brand_hex = _generate_brand_hex(f"{idea.title}{idea.description}")
    
    _IDEAS[idea.idea_id] = idea
    _flush()
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
            "tier": idea.tier,
            "brand_hex": idea.brand_hex,
        }
        for idea in _IDEAS.values()
    ]


def import_ideas_snapshot(rows: object) -> None:
    if not isinstance(rows, list):
        return
    _IDEAS.clear()
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            idea = Idea(
                title=row["title"],
                description=row["description"],
                target_user=row["target_user"],
                context=row["context"],
                tier=row.get("tier", "Bronze"),
                brand_hex=row.get("brand_hex", "#888888"),
            )
            idea.idea_id = UUID(row["idea_id"])
            idea.created_at = datetime.fromisoformat(row["created_at"])
            _IDEAS[idea.idea_id] = idea
        except (KeyError, ValueError) as e:
            LOGGER.error(f"Failed to import idea row: {e}")


# Auto-initialize on import
initialize()
