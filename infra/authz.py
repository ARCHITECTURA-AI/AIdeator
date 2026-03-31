"""PH-C authorization helpers for row-level user scope."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def enforce_user_scope(*, actor_user_id: str, row_user_id: str | None, resource_id: str) -> None:
    """Raise when a caller attempts to access data outside its user scope."""
    if row_user_id is None:
        raise PermissionError(f"Resource {resource_id} has no user scope")
    if actor_user_id != row_user_id:
        raise PermissionError(
            f"User scope violation for resource {resource_id}: "
            f"{actor_user_id} cannot access {row_user_id}"
        )


def assert_row_scope(actor_user_id: str, row: Mapping[str, Any]) -> None:
    """Extract a row owner field and enforce the caller scope."""
    row_user_id = row.get("target_user") or row.get("user_id") or row.get("owner_user_id")
    resource_id = str(row.get("idea_id") or row.get("run_id") or row.get("id") or "<unknown>")
    enforce_user_scope(
        actor_user_id=actor_user_id,
        row_user_id=str(row_user_id) if row_user_id is not None else None,
        resource_id=resource_id,
    )
