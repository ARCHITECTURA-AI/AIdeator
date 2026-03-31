"""Sandbox helpers that constrain plugin capabilities."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

ALLOWED_CAPABILITIES = frozenset({"signals:read", "signals:emit"})
ALLOWED_FILE_ROOT = (Path(__file__).resolve().parents[1] / "docs").resolve()
ALLOWED_NETWORK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def assert_plugin_caps(capabilities: list[str] | tuple[str, ...] | set[str]) -> bool:
    """Return True only when all requested caps are on the allow-list."""
    requested = {str(cap) for cap in capabilities}
    return requested.issubset(ALLOWED_CAPABILITIES)


def enforce_plugin_policy(*, action: str, target: str) -> bool:
    """Block DB writes and arbitrary file/network access from plugins."""
    normalized_action = action.strip().lower()

    if normalized_action == "db_write":
        return False

    if normalized_action == "file_read":
        candidate = Path(target).resolve()
        return candidate == ALLOWED_FILE_ROOT or ALLOWED_FILE_ROOT in candidate.parents

    if normalized_action == "network_call":
        hostname = (urlparse(target).hostname or "").lower()
        return hostname in ALLOWED_NETWORK_HOSTS

    return False
