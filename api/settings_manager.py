"""Settings persistence manager."""

import logging
from pathlib import Path
from typing import Any
from db.base import BaseJsonStorage
from api.config import settings as app_settings

_STORAGE_PATH = Path("data/settings.json")
_STORAGE = BaseJsonStorage(_STORAGE_PATH, "api.settings")
LOGGER = logging.getLogger("api.settings")

# Initial defaults from app config
_SETTINGS: dict[str, Any] = {
    "default_mode": app_settings.app_default_mode,
    "allow_cloud": False,
    "telemetry_enabled": False,
    "api_keys_configured": False,
}

def _import_settings(data: object) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in _SETTINGS:
                _SETTINGS[key] = value

def _export_settings() -> dict[str, Any]:
    return _SETTINGS

def initialize():
    """Load settings from disk."""
    if _STORAGE_PATH.exists():
        _STORAGE.load(_import_settings)
    else:
        # Save defaults if no file exists
        save_settings()

def get_settings() -> dict[str, Any]:
    """Get all current settings."""
    return _SETTINGS

def update_settings(payload: dict[str, Any]) -> dict[str, Any]:
    """Update settings and persist to disk."""
    for key, value in payload.items():
        if key in _SETTINGS:
            _SETTINGS[key] = value
    save_settings()
    return _SETTINGS

def save_settings():
    """Flush settings to disk."""
    _STORAGE.flush(_export_settings)

# Auto-initialize on first import
initialize()
