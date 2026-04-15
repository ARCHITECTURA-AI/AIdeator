"""Unit tests for cross-platform path utilities."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from aideator.paths import (
    APP_NAME,
    ensure_dir,
    get_all_paths,
    get_cache_dir,
    get_default_config_path,
    get_default_db_path,
    get_default_docs_dir,
    get_user_data_dir,
    resolve_path,
)


class TestGetUserDataDir:
    """Tests for OS-correct path resolution."""

    def test_returns_path_object(self) -> None:
        result = get_user_data_dir()
        assert isinstance(result, Path)

    def test_contains_app_name(self) -> None:
        result = get_user_data_dir()
        assert APP_NAME in str(result)

    @patch("aideator.paths.platform.system", return_value="Windows")
    def test_windows_uses_appdata(self, mock_sys: object) -> None:
        with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
            result = get_user_data_dir()
            assert "AppData" in str(result) or "appdata" in str(result).lower()

    @patch("aideator.paths.platform.system", return_value="Darwin")
    def test_macos_uses_library(self, mock_sys: object) -> None:
        result = get_user_data_dir()
        assert "Library" in str(result) or "Application Support" in str(result)

    @patch("aideator.paths.platform.system", return_value="Linux")
    def test_linux_uses_xdg_or_local(self, mock_sys: object) -> None:
        # Remove XDG_DATA_HOME but keep HOME/USERPROFILE for Path.home()
        env_override = {k: v for k, v in os.environ.items()}
        env_override.pop("XDG_DATA_HOME", None)
        with patch.dict(os.environ, env_override, clear=True):
            result = get_user_data_dir()
            assert ".local" in str(result) or f".{APP_NAME}" in str(result)


class TestDefaultPaths:
    """Tests for default DB, docs, and config paths."""

    def test_db_path_ends_with_db(self) -> None:
        result = get_default_db_path()
        assert str(result).endswith("aideator.db")

    def test_docs_dir_ends_with_docs(self) -> None:
        result = get_default_docs_dir()
        assert str(result).endswith("docs")

    def test_config_path_ends_with_toml(self) -> None:
        result = get_default_config_path()
        assert str(result).endswith("config.toml")


class TestEnsureDir:
    """Tests for lazy directory creation."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "test_ensure" / "nested"
        assert not new_dir.exists()
        result = ensure_dir(new_dir)
        assert new_dir.exists()
        assert result == new_dir

    def test_idempotent(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "test_idem"
        ensure_dir(new_dir)
        ensure_dir(new_dir)  # Should not raise
        assert new_dir.exists()


class TestResolvePath:
    """Tests for path resolution."""

    def test_resolves_tilde(self) -> None:
        result = resolve_path("~/test")
        assert "~" not in str(result)

    def test_accepts_path_object(self) -> None:
        result = resolve_path(Path("./test"))
        assert isinstance(result, Path)
        assert result.is_absolute()


class TestGetAllPaths:
    """Tests for path dictionary."""

    def test_returns_all_keys(self) -> None:
        paths = get_all_paths()
        expected_keys = {"user_data_dir", "db_path", "docs_dir", "config_path", "migrations_dir", "logs_dir", "cache_dir"}
        assert expected_keys == set(paths.keys())

    def test_all_values_are_paths(self) -> None:
        paths = get_all_paths()
        for key, value in paths.items():
            assert isinstance(value, Path), f"{key} is not a Path"
