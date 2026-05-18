import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import (  # type: ignore[attr-defined, unused-ignore]
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


class IdeaModel(Base):
    __tablename__ = "ideas"
    idea_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    target_user: Mapped[str] = mapped_column(String(255), nullable=False)
    context: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    tier: Mapped[str | None] = mapped_column(String(50), default="Bronze")
    brand_hex: Mapped[str | None] = mapped_column(String(7), default="#888888")
    validation_status: Mapped[str] = mapped_column(String(50), default="desk_research")
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=True
    )
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workspaces.workspace_id"), nullable=True
    )


class UserModel(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class RunModel(Base):
    __tablename__ = "runs"
    run_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    idea_id: Mapped[str] = mapped_column(String(36), ForeignKey("ideas.idea_id"), nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ReportModel(Base):
    __tablename__ = "reports"
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.run_id"), primary_key=True)
    cards: Mapped[dict] = mapped_column(JSON, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String, nullable=False)
    citations: Mapped[list] = mapped_column(JSON, nullable=False, default=[])
    battle_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    interview_kit: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    experiment_kit: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SignalModel(Base):
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.run_id"), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)


class CommentModel(Base):
    __tablename__ = "comments"
    comment_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    idea_id: Mapped[str] = mapped_column(String(36), ForeignKey("ideas.idea_id"), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class WorkspaceModel(Base):
    __tablename__ = "workspaces"
    workspace_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class WorkspaceMemberModel(Base):
    __tablename__ = "workspace_members"
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.workspace_id"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), primary_key=True)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="viewer"
    )  # viewer, editor, admin
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class WebhookModel(Base):
    __tablename__ = "webhooks"
    webhook_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.user_id"), nullable=True
    )  # User or Workspace owner
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workspaces.workspace_id"), nullable=True
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    events: Mapped[str] = mapped_column(String, nullable=False, default="run.succeeded")
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class TemplateModel(Base):
    __tablename__ = "templates"
    template_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    prefilled_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), nullable=False)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    is_public: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class TemplateUpvoteModel(Base):
    __tablename__ = "template_upvotes"
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("templates.template_id"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
