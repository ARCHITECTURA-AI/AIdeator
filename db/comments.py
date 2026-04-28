"""SQLite-backed comments repository."""

from __future__ import annotations

import logging
from uuid import UUID

from db.base import db_session, initialize_db
from db.schema import CommentModel
from models.comment import Comment

LOGGER = logging.getLogger("db.comments")


def initialize():
    initialize_db()


def _to_model(comment: Comment) -> CommentModel:
    return CommentModel(
        comment_id=str(comment.comment_id),
        idea_id=str(comment.idea_id),
        author=comment.author,
        content=comment.content,
        created_at=comment.created_at,
    )


def _from_model(model: CommentModel) -> Comment:
    c = Comment(
        idea_id=UUID(model.idea_id),
        author=model.author,
        content=model.content,
    )
    c.comment_id = UUID(model.comment_id)
    c.created_at = model.created_at
    return c


def add_comment(comment: Comment) -> Comment:
    session = db_session()
    try:
        model = _to_model(comment)
        session.add(model)
        session.commit()
        return comment
    except Exception as e:
        session.rollback()
        LOGGER.error(f"Failed to add comment: {e}")
        raise e
    finally:
        db_session.remove()


def list_comments_for_idea(idea_id: UUID) -> list[Comment]:
    session = db_session()
    try:
        models = (
            session.query(CommentModel)
            .filter_by(idea_id=str(idea_id))
            .order_by(CommentModel.created_at.asc())
            .all()
        )
        return [_from_model(m) for m in models]
    finally:
        db_session.remove()


# Legacy snapshot functions
def export_comments_snapshot():
    return []


def import_comments_snapshot(rows):
    pass


# initialize() - REMOVED
