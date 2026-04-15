import json
import logging
from pathlib import Path
from typing import Final
from uuid import UUID
from db.base import BaseJsonStorage

_STORAGE_PATH: Final[Path] = Path("data/signals.json")
_SIGNALS: Final[dict[UUID, list[dict[str, str]]]] = {}
_STORAGE = BaseJsonStorage(_STORAGE_PATH, "db.signals")
LOGGER = logging.getLogger("db.signals")


def _flush():
    """Flush signals to disk."""
    _STORAGE.flush(export_signals_snapshot)


def initialize():
    """Load signals from disk."""
    _STORAGE.load(import_signals_snapshot)


def save_signal(run_id: UUID, signal: dict[str, str]) -> None:
    _SIGNALS.setdefault(run_id, []).append(signal)
    _flush()


def list_signals(run_id: UUID) -> list[dict[str, str]]:
    return list(_SIGNALS.get(run_id, []))


def export_signals_snapshot() -> dict[str, list[dict[str, str]]]:
    return {str(run_id): list(signals) for run_id, signals in _SIGNALS.items()}


def import_signals_snapshot(snapshot: object) -> None:
    if not isinstance(snapshot, dict):
        return
    _SIGNALS.clear()
    for run_id, signals in snapshot.items():
        if not isinstance(signals, list):
            continue
        try:
            _SIGNALS[UUID(run_id)] = list(signals)
        except ValueError:
            continue


# Auto-initialize on import
initialize()
