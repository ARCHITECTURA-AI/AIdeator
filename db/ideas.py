"""SQLite-backed ideas repository."""

from __future__ import annotations

import logging
from uuid import UUID

from db.base import db_session, initialize_db
from db.schema import IdeaModel, WorkspaceMemberModel
from models.idea import Idea

LOGGER = logging.getLogger("db.ideas")


def initialize():
    """Ensure DB is ready."""
    initialize_db()


def _to_model(idea: Idea) -> IdeaModel:
    return IdeaModel(
        idea_id=str(idea.idea_id),
        title=idea.title,
        description=idea.description,
        target_user=idea.target_user,
        context=idea.context,
        created_at=idea.created_at,
        tier=idea.tier,
        brand_hex=idea.brand_hex,
        workspace_id=str(idea.workspace_id) if idea.workspace_id else None,
    )


def _from_model(model: IdeaModel) -> Idea:
    idea = Idea(
        title=model.title,
        description=model.description,
        target_user=model.target_user,
        context=model.context,
        tier=model.tier or "Bronze",
        brand_hex=model.brand_hex or "#888888",
        workspace_id=UUID(model.workspace_id) if model.workspace_id else None,
    )
    idea.idea_id = UUID(model.idea_id)
    idea.created_at = model.created_at
    return idea


def save_idea(idea: Idea, user_id: UUID | None = None) -> Idea:
    session = db_session()
    try:
        model = session.query(IdeaModel).filter_by(idea_id=str(idea.idea_id)).first()
        if model:
            model.title = idea.title
            model.description = idea.description
            model.target_user = idea.target_user
            model.context = idea.context
            model.tier = idea.tier
            model.brand_hex = idea.brand_hex
            if idea.workspace_id:
                model.workspace_id = str(idea.workspace_id)
            if user_id:
                model.user_id = str(user_id)
        else:
            model = _to_model(idea)
            if user_id:
                model.user_id = str(user_id)
            session.add(model)
        session.commit()
        return idea
    except Exception as e:
        session.rollback()
        LOGGER.error(f"Failed to save idea: {e}")
        raise e
    finally:
        db_session.remove()


def get_idea(idea_id: UUID) -> Idea | None:
    session = db_session()
    try:
        model = session.query(IdeaModel).filter_by(idea_id=str(idea_id)).first()
        return _from_model(model) if model else None
    finally:
        db_session.remove()


def list_ideas(user_id: UUID | None = None) -> list[Idea]:
    session = db_session()
    try:
        query = session.query(IdeaModel)
        if user_id:
            # Shared ideas: user is owner OR user is member of the workspace
            from sqlalchemy import or_

            workspace_ids = [
                m.workspace_id
                for m in session.query(WorkspaceMemberModel).filter_by(user_id=str(user_id)).all()
            ]
            query = query.filter(
                or_(IdeaModel.user_id == str(user_id), IdeaModel.workspace_id.in_(workspace_ids))
            )
        models = query.order_by(IdeaModel.created_at.desc()).all()
        return [_from_model(m) for m in models]
    finally:
        db_session.remove()


# Legacy snapshot functions for compatibility (empty for now)
def export_ideas_snapshot():
    return []


def import_ideas_snapshot(rows):
    pass


# Initialize on import - REMOVED to prevent race conditions in tests.
# The app or CLI should call initialize_db() explicitly.
