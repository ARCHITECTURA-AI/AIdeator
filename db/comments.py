"""In-memory comments repository."""

from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, List
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from db.base import BaseJsonStorage

@dataclass
class Comment:
    idea_id: UUID
    author: str
    content: str
    comment_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

_STORAGE_PATH: Final[Path] = Path("data/comments.json")
_COMMENTS: Final[List[Comment]] = []
_STORAGE = BaseJsonStorage(_STORAGE_PATH, "db.comments")
LOGGER = logging.getLogger("db.comments")

def _flush():
    _STORAGE.flush(export_comments_snapshot)

def initialize():
    _STORAGE.load(import_comments_snapshot)

def add_comment(comment: Comment) -> Comment:
    _COMMENTS.append(comment)
    _flush()
    return comment

def list_comments_for_idea(idea_id: UUID) -> List[Comment]:
    return [c for c in _COMMENTS if c.idea_id == idea_id]

def export_comments_snapshot() -> list[dict[str, str]]:
    return [
        {
            "comment_id": str(c.comment_id),
            "idea_id": str(c.idea_id),
            "author": c.author,
            "content": c.content,
            "created_at": c.created_at.isoformat(),
        }
        for c in _COMMENTS
    ]

def import_comments_snapshot(rows: object) -> None:
    if not isinstance(rows, list):
        return
    _COMMENTS.clear()
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            c = Comment(
                idea_id=UUID(row["idea_id"]),
                author=row["author"],
                content=row["content"],
                comment_id=UUID(row["comment_id"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            _COMMENTS.append(c)
        except (KeyError, ValueError) as e:
            LOGGER.error(f"Failed to import comment row: {e}")

initialize()
