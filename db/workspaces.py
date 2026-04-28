"""Workspace repository."""

from __future__ import annotations

from uuid import UUID, uuid4

from db.base import db_session
from db.schema import UserModel, WorkspaceMemberModel, WorkspaceModel


def create_workspace(name: str, owner_id: UUID) -> str:
    session = db_session()
    try:
        ws_id = str(uuid4())
        ws = WorkspaceModel(workspace_id=ws_id, name=name, owner_id=str(owner_id))
        session.add(ws)

        # Owner is automatically an admin member
        member = WorkspaceMemberModel(workspace_id=ws_id, user_id=str(owner_id), role="admin")
        session.add(member)

        session.commit()
        return ws_id
    finally:
        db_session.remove()


def add_member(workspace_id: str, email: str, role: str) -> bool:
    session = db_session()
    try:
        user = session.query(UserModel).filter_by(email=email).first()
        if not user:
            return False

        # Check if already a member
        existing = (
            session.query(WorkspaceMemberModel)
            .filter_by(workspace_id=workspace_id, user_id=user.user_id)
            .first()
        )
        if existing:
            existing.role = role
        else:
            member = WorkspaceMemberModel(
                workspace_id=workspace_id, user_id=user.user_id, role=role
            )
            session.add(member)

        session.commit()
        return True
    finally:
        db_session.remove()


def get_user_workspaces(user_id: UUID) -> list[dict[str, str]]:
    session = db_session()
    try:
        memberships = session.query(WorkspaceMemberModel).filter_by(user_id=str(user_id)).all()
        ws_ids = [m.workspace_id for m in memberships]
        workspaces = (
            session.query(WorkspaceModel).filter(WorkspaceModel.workspace_id.in_(ws_ids)).all()
        )
        return [{"workspace_id": w.workspace_id, "name": w.name} for w in workspaces]
    finally:
        db_session.remove()


def is_member(workspace_id: str, user_id: str) -> str | None:
    session = db_session()
    try:
        member = (
            session.query(WorkspaceMemberModel)
            .filter_by(workspace_id=workspace_id, user_id=user_id)
            .first()
        )
        return member.role if member else None
    finally:
        db_session.remove()
