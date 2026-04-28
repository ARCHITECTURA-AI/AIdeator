"""Template repository."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from db.base import db_session
from db.schema import TemplateModel, TemplateUpvoteModel


def create_template(
    title: str, description: str, category: str, prefilled_data: dict[str, Any], author_id: UUID
) -> str:
    session = db_session()
    try:
        t_id = str(uuid4())
        template = TemplateModel(
            template_id=t_id,
            title=title,
            description=description,
            category=category,
            prefilled_data=prefilled_data,
            author_id=str(author_id),
        )
        session.add(template)
        session.commit()
        return t_id
    finally:
        db_session.remove()


def list_public_templates() -> list[dict[str, Any]]:
    session = db_session()
    try:
        templates = (
            session.query(TemplateModel)
            .filter_by(is_public=1)
            .order_by(TemplateModel.upvotes.desc())
            .all()
        )
        return [
            {
                "template_id": t.template_id,
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "upvotes": t.upvotes,
                "author_id": t.author_id,
            }
            for t in templates
        ]
    finally:
        db_session.remove()


def get_template_details(template_id: str) -> dict[str, Any] | None:
    session = db_session()
    try:
        t = session.query(TemplateModel).filter_by(template_id=template_id).first()
        if not t:
            return None
        return {
            "template_id": t.template_id,
            "title": t.title,
            "description": t.description,
            "category": t.category,
            "prefilled_data": t.prefilled_data,
            "upvotes": t.upvotes,
            "author_id": t.author_id,
            "created_at": t.created_at.isoformat(),
        }
    finally:
        db_session.remove()


def upvote_template(template_id: str, user_id: UUID) -> int:
    session = db_session()
    try:
        # Check if already upvoted
        existing = (
            session.query(TemplateUpvoteModel)
            .filter_by(template_id=template_id, user_id=str(user_id))
            .first()
        )
        if existing:
            t = session.query(TemplateModel).filter_by(template_id=template_id).first()
            return t.upvotes if t else 0

        # Add upvote
        upvote = TemplateUpvoteModel(template_id=template_id, user_id=str(user_id))
        session.add(upvote)

        # Increment counter
        template = session.query(TemplateModel).filter_by(template_id=template_id).first()
        if template:
            template.upvotes += 1
            upvotes = template.upvotes
            session.commit()
            return upvotes
        return 0
    finally:
        db_session.remove()
