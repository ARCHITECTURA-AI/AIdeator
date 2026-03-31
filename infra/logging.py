"""Structured logging utilities with basic redaction."""

from __future__ import annotations

REDACTED_KEYS = {"idea_title", "idea_description", "signal_snippet"}


def sanitize_log_event(event: dict[str, object]) -> dict[str, object]:
    sanitized = dict(event)
    for key in REDACTED_KEYS:
        if key in sanitized:
            sanitized[key] = "[REDACTED]"
    return sanitized


def redact_log_payload(event: dict[str, object]) -> dict[str, object]:
    return sanitize_log_event(event)
