"""Path utilities for AIdeator user data directories.

Provides cross-platform path resolution for user data, config, and docs.
Follows XDG Base Directory Specification on Linux/macOS and uses
APPDATA on Windows.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

APP_NAME = "aideator"


def get_user_data_dir() -> Path:
    """Return the user data directory for AIdeator.

    Platform-specific locations:
    - macOS: ~/Library/Application Support/aideator/
    - Linux/Unix: ~/.local/share/aideator/ (fallback ~/.aideator/)
    - Windows: %APPDATA%\aideator\
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        base_dir = Path.home() / "Library" / "Application Support"
        data_dir = base_dir / APP_NAME
    elif system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            data_dir = Path(appdata) / APP_NAME
        else:
            data_dir = Path.home() / "AppData" / "Roaming" / APP_NAME
    else:  # Linux and other Unix
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            data_dir = Path(xdg_data_home) / APP_NAME
        else:
            # XDG fallback or legacy ~/.aideator
            xdg_fallback = Path.home() / ".local" / "share" / APP_NAME
            legacy_path = Path.home() / f".{APP_NAME}"
            # Prefer XDG, but check if legacy exists
            if legacy_path.exists() and not xdg_fallback.exists():
                data_dir = legacy_path
            else:
                data_dir = xdg_fallback

    return data_dir


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_default_db_path() -> Path:
    """Return the default database file path.

    Returns: <user_data_dir>/aideator.db
    """
    return get_user_data_dir() / "aideator.db"


def get_default_docs_dir() -> Path:
    """Return the default docs directory path.

    Returns: <user_data_dir>/docs/
    """
    return get_user_data_dir() / "docs"


def get_default_config_path() -> Path:
    """Return the default config file path.

    Returns: <user_data_dir>/config.toml
    """
    return get_user_data_dir() / "config.toml"


def get_migrations_dir() -> Path:
    """Return the migrations directory path.

    Returns: <user_data_dir>/migrations/
    """
    return get_user_data_dir() / "migrations"


def get_logs_dir() -> Path:
    """Return the logs directory path.

    Returns: <user_data_dir>/logs/
    """
    return get_user_data_dir() / "logs"


def get_cache_dir() -> Path:
    """Return the cache directory path.

    Platform-specific cache location:
    - macOS: ~/Library/Caches/aideator/
    - Linux/Unix: ~/.cache/aideator/
    - Windows: %LOCALAPPDATA%\\aideator\\Cache\\
    """
    system = platform.system()

    if system == "Darwin":
        base_dir = Path.home() / "Library" / "Caches"
        cache_dir = base_dir / APP_NAME
    elif system == "Windows":
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            cache_dir = Path(localappdata) / APP_NAME / "Cache"
        else:
            cache_dir = Path.home() / "AppData" / "Local" / APP_NAME / "Cache"
    else:  # Linux and other Unix
        xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache_home:
            cache_dir = Path(xdg_cache_home) / APP_NAME
        else:
            cache_dir = Path.home() / ".cache" / APP_NAME

    return cache_dir


def resolve_path(path_str: str | Path) -> Path:
    """Resolve a path string, expanding ~ and environment variables.

    Args:
        path_str: Path string that may contain ~ or env vars

    Returns:
        Resolved Path object
    """
    if isinstance(path_str, Path):
        return path_str.expanduser().resolve()

    expanded = os.path.expandvars(os.path.expanduser(path_str))
    return Path(expanded).resolve()


def get_all_paths() -> dict[str, Path]:
    """Return a dictionary of all standard paths.

    Useful for debugging and config display.
    """
    return {
        "user_data_dir": get_user_data_dir(),
        "db_path": get_default_db_path(),
        "docs_dir": get_default_docs_dir(),
        "config_path": get_default_config_path(),
        "migrations_dir": get_migrations_dir(),
        "logs_dir": get_logs_dir(),
        "cache_dir": get_cache_dir(),
    }


def get_report_path_for_idea(idea_id: Any, docs_dir: Path | None = None) -> Path:
    """Return the markdown report path for a specific idea."""
    from api.config import settings
    base = docs_dir or settings.app_docs_dir
    return base / f"idea-{idea_id}.md"
