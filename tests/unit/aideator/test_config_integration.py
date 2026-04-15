"""Unit tests for config integration."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from api.config import (
    Settings,
    _default_mode_from_env,
    _parse_bool,
    _redact_sensitive,
    _resolve_db_url,
    load_config_file,
    load_settings,
)


class TestDefaultModeFromEnv:
    """Tests for mode mapping."""

    def test_local_maps_to_local_only(self) -> None:
        assert _default_mode_from_env("local") == "local-only"

    def test_local_only_direct(self) -> None:
        assert _default_mode_from_env("local-only") == "local-only"

    def test_hybrid(self) -> None:
        assert _default_mode_from_env("hybrid") == "hybrid"

    def test_cloud_maps_to_cloud_enabled(self) -> None:
        assert _default_mode_from_env("cloud") == "cloud-enabled"

    def test_cloud_enabled_direct(self) -> None:
        assert _default_mode_from_env("cloud-enabled") == "cloud-enabled"

    def test_unknown_defaults_to_local_only(self) -> None:
        assert _default_mode_from_env("invalid") == "local-only"

    def test_case_insensitive(self) -> None:
        assert _default_mode_from_env("HYBRID") == "hybrid"

    def test_whitespace_stripped(self) -> None:
        assert _default_mode_from_env("  cloud  ") == "cloud-enabled"


class TestParseBool:
    """Tests for boolean parsing."""

    def test_true_values(self) -> None:
        for val in ("1", "true", "True", "TRUE", "yes", "on"):
            assert _parse_bool(val) is True, f"Expected True for {val}"

    def test_false_values(self) -> None:
        for val in ("0", "false", "no", "off", "anything"):
            assert _parse_bool(val) is False, f"Expected False for {val}"

    def test_none_returns_default(self) -> None:
        assert _parse_bool(None, default=False) is False
        assert _parse_bool(None, default=True) is True


class TestRedactSensitive:
    """Tests for secret redaction."""

    def test_redacts_long_keys(self) -> None:
        result = _redact_sensitive("sk-1234567890abcdef")
        assert "sk-1" in result
        assert "cdef" in result
        assert "567890" not in result

    def test_short_keys_fully_redacted(self) -> None:
        result = _redact_sensitive("abc")
        assert result == "***"

    def test_empty_string(self) -> None:
        assert _redact_sensitive("") == "***"


class TestResolveDbUrl:
    """Tests for DB URL resolution."""

    def test_sqlite_memory_unchanged(self) -> None:
        url = "sqlite:///:memory:"
        assert _resolve_db_url(url) == url

    def test_absolute_path_unchanged(self) -> None:
        if os.name == "nt":
            url = "sqlite:///C:/data/test.db"
        else:
            url = "sqlite:////data/test.db"
        result = _resolve_db_url(url)
        assert result.startswith("sqlite:///")


class TestLoadConfigFile:
    """Tests for TOML config file loading."""

    def test_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        result = load_config_file(tmp_path / "missing.toml")
        assert result == {}

    def test_valid_toml_parsed(self, tmp_path: Path) -> None:
        config_file = tmp_path / "test.toml"
        config_file.write_text('[core]\ndefault_mode = "hybrid"\n', encoding="utf-8")
        result = load_config_file(config_file)
        assert result["core"]["default_mode"] == "hybrid"

    def test_malformed_toml_returns_empty(self, tmp_path: Path) -> None:
        config_file = tmp_path / "bad.toml"
        config_file.write_text("this is not [valid toml\n", encoding="utf-8")
        result = load_config_file(config_file)
        assert result == {}


class TestLoadSettings:
    """Tests for full settings loading."""

    def test_settings_type(self) -> None:
        s = load_settings()
        assert isinstance(s, Settings)

    def test_default_mode_is_run_mode(self) -> None:
        s = load_settings()
        assert s.app_default_mode in ("local-only", "hybrid", "cloud-enabled")

    def test_search_provider_has_default(self) -> None:
        s = load_settings()
        assert s.search_provider in ("builtin", "duckduckgo", "searxng", "tavily", "exa")

    def test_llm_provider_has_default(self) -> None:
        s = load_settings()
        assert s.llm_provider  # Non-empty

    def test_to_dict_redacts_secrets(self) -> None:
        s = load_settings()
        d = s.to_dict(redact_secrets=True)
        # LLM key should be redacted
        assert d["llm"]["api_key"] == "***" or "..." in d["llm"]["api_key"]

    def test_cli_db_url_override(self) -> None:
        s = load_settings(cli_db_url="sqlite:///:memory:")
        assert s.app_db_url == "sqlite:///:memory:"

    def test_cli_docs_dir_override(self, tmp_path: Path) -> None:
        docs = tmp_path / "test_docs"
        s = load_settings(cli_docs_dir=str(docs))
        assert Path(s.app_docs_dir) == docs.resolve()

    def test_get_effective_search_api_key_builtin(self) -> None:
        s = load_settings()
        if s.search_provider == "builtin":
            assert s.get_effective_search_api_key() == ""
