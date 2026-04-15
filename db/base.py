"""Thread-safe, atomic JSON storage base."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from threading import Lock
from typing import Generic, TypeVar, Callable

T = TypeVar("T")

class BaseJsonStorage(Generic[T]):
    """Atomic and thread-safe JSON storage base class."""

    def __init__(self, storage_path: Path, logger_name: str):
        self._path = storage_path
        self._logger = logging.getLogger(logger_name)
        self._lock = Lock()
        self._data: dict[str, T] = {}

    def _atomic_write(self, data: object) -> None:
        """Write data to disk atomically using a temp file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # mode "w", delete=False to allow os.replace on Windows
        fd, temp_path = tempfile.mkstemp(
            dir=self._path.parent,
            prefix=f"{self._path.name}.tmp",
            suffix=".json",
            text=True
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            # Atomic replace
            if os.path.exists(self._path):
                os.replace(temp_path, self._path)
            else:
                os.rename(temp_path, self._path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e

    def load(self, import_func: Callable[[object], None]) -> None:
        """Load data from disk."""
        with self._lock:
            if not self._path.exists():
                return
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                import_func(raw_data)
                self._logger.info(f"Loaded storage from {self._path}")
            except Exception as e:
                self._logger.error(f"Failed to load storage from {self._path}: {e}")

    def flush(self, export_func: Callable[[], object]) -> None:
        """Flush current memory state to disk."""
        with self._lock:
            try:
                data = export_func()
                self._atomic_write(data)
            except Exception as e:
                self._logger.error(f"Failed to flush storage to {self._path}: {e}")
