"""SQLite-backed users repository."""

from __future__ import annotations

import logging
from uuid import UUID

from db.base import db_session, initialize_db
from db.schema import UserModel
from models.user import User

LOGGER = logging.getLogger("db.users")


def initialize():
    """Ensure DB is ready."""
    initialize_db()


def _to_model(user: User) -> UserModel:
    return UserModel(
        user_id=str(user.user_id),
        email=user.email,
        hashed_password=user.hashed_password,
        full_name=user.full_name,
        created_at=user.created_at,
    )


def _from_model(model: UserModel) -> User:
    user = User(email=model.email, hashed_password=model.hashed_password, full_name=model.full_name)
    user.user_id = UUID(model.user_id)
    user.created_at = model.created_at
    return user


def save_user(user: User) -> User:
    session = db_session()
    try:
        model = session.query(UserModel).filter_by(user_id=str(user.user_id)).first()
        if model:
            model.email = user.email
            model.hashed_password = user.hashed_password
            model.full_name = user.full_name
        else:
            model = _to_model(user)
            session.add(model)
        session.commit()
        return user
    except Exception as e:
        session.rollback()
        LOGGER.error(f"Failed to save user: {e}")
        raise e
    finally:
        db_session.remove()


def get_user_by_email(email: str) -> User | None:
    session = db_session()
    try:
        model = session.query(UserModel).filter_by(email=email).first()
        return _from_model(model) if model else None
    finally:
        db_session.remove()


def get_user(user_id: UUID) -> User | None:
    session = db_session()
    try:
        model = session.query(UserModel).filter_by(user_id=str(user_id)).first()
        return _from_model(model) if model else None
    finally:
        db_session.remove()


# Initialize on import
initialize()
