"""In-memory signals repository."""

from __future__ import annotations

from typing import Final
from uuid import UUID

_SIGNALS: Final[dict[UUID, list[dict[str, str]]]] = {}


def save_signal(run_id: UUID, signal: dict[str, str]) -> None:
    _SIGNALS.setdefault(run_id, []).append(signal)


def list_signals(run_id: UUID) -> list[dict[str, str]]:
    return list(_SIGNALS.get(run_id, []))


def export_signals_snapshot() -> dict[str, list[dict[str, str]]]:
    return {str(run_id): list(signals) for run_id, signals in _SIGNALS.items()}


def import_signals_snapshot(snapshot: dict[str, list[dict[str, str]]]) -> None:
    _SIGNALS.clear()
    for run_id, signals in snapshot.items():
        _SIGNALS[UUID(run_id)] = list(signals)
