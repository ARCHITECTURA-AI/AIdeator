"""Unit tests for api.config module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from aideator.paths import get_default_config_path, get_default_db_path, get_default_docs_dir


def preserve_home_env():
    """Get environment dict that preserves HOME/USERPROFILE."""
    env = {}
    for key in ["HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"]:
        if key in os.environ:
            env[key] = os.environ[key]
    return env


class TestLoadConfigFile:
    """Tests for load_config_file function."""

    def test_returns_empty_dict_when_no_file(self, tmp_path: Path):
        """Should return empty dict when config file doesn't exist."""
        from api.config import load_config_file

        nonexistent_path = tmp_path / "nonexistent.toml"
        result = load_config_file(nonexistent_path)
        assert result == {}

    def test_loads_valid_toml(self, tmp_path: Path):
        """Should load valid TOML config file."""
        from api.config import load_config_file

        config_path = tmp_path / "test_config.toml"
        config_path.write_text(
            """
[core]
default_mode = "hybrid"

[storage]
db_url = "sqlite:///test.db"
docs_dir = "/test/docs"

[llm]
provider = "ollama"
model = "llama2"
"""
        )
        result = load_config_file(config_path)
        assert result["core"]["default_mode"] == "hybrid"
        assert result["storage"]["db_url"] == "sqlite:///test.db"
        assert result["llm"]["provider"] == "ollama"

    def test_returns_empty_dict_on_malformed_toml(self, tmp_path: Path):
        """Should return empty dict on malformed TOML."""
        from api.config import load_config_file

        config_path = tmp_path / "bad_config.toml"
        config_path.write_text("[invalid toml [[[")
        result = load_config_file(config_path)
        assert result == {}


class TestLoadSettings:
    """Tests for load_settings function."""

    def test_uses_defaults_when_no_config(self, tmp_path: Path):
        """Should use default values when no config exists."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                assert settings.app_env == "local"
                assert settings.app_default_mode == "local-only"
                assert settings.llm_provider == "ollama"
                assert settings.search_provider == "duckduckgo"

    def test_env_overrides_defaults(self, tmp_path: Path):
        """Environment variables should override defaults."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env.update({
            "APP_ENV": "prod",
            "APP_DEFAULT_MODE": "hybrid",
            "LLM_PROVIDER": "openai-compatible",
            "SEARCH_PROVIDER": "tavily",
        })
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                assert settings.app_env == "prod"
                assert settings.app_default_mode == "hybrid"
                assert settings.llm_provider == "openai-compatible"
                assert settings.search_provider == "tavily"

    def test_cli_overrides_env(self, tmp_path: Path):
        """CLI arguments should override environment variables."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env.update({
            "APP_DB_URL": "sqlite:///env.db",
            "APP_DOCS_DIR": "/env/docs",
        })
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                with mock.patch("pathlib.Path.mkdir"):
                    settings = load_settings(
                        cli_db_url="sqlite:///cli.db", cli_docs_dir="/cli/docs", load_env=False
                    )
                    assert "cli.db" in settings.app_db_url
                    assert "/cli/docs" in str(settings.app_docs_dir) or "\\cli\\docs" in str(settings.app_docs_dir)

    def test_config_file_values_used(self, tmp_path: Path):
        """Config file values should be used when no env override."""
        from api.config import load_settings

        config_path = tmp_path / "aideator.toml"
        config_path.write_text(
            """
[core]
default_mode = "cloud-enabled"

[llm]
provider = "mistral-compatible"
model = "mistral-large"

[search]
provider = "exa"
"""
        )

        base_env = preserve_home_env()
        with mock.patch.dict(os.environ, base_env, clear=True):
            with mock.patch("pathlib.Path.mkdir"):
                settings = load_settings(cli_config_path=config_path, load_env=False)
                assert settings.app_default_mode == "cloud-enabled"
                assert settings.llm_provider == "mistral-compatible"
                assert settings.llm_model == "mistral-large"
                assert settings.search_provider == "exa"

    def test_env_overrides_config_file(self, tmp_path: Path):
        """Environment variables should override config file."""
        from api.config import load_settings

        config_path = tmp_path / "aideator.toml"
        config_path.write_text(
            """
[llm]
provider = "ollama"
model = "mistral:7b"
"""
        )

        base_env = preserve_home_env()
        base_env["LLM_PROVIDER"] = "openai-compatible"
        with mock.patch.dict(os.environ, base_env, clear=True):
            settings = load_settings(cli_config_path=config_path, load_env=False)
            assert settings.llm_provider == "openai-compatible"

    def test_db_url_expands_tilde(self, tmp_path: Path):
        """Should expand ~ in database URL paths."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                with mock.patch("pathlib.Path.mkdir"):
                    settings = load_settings(cli_db_url="sqlite:///~/.aideator/test.db", load_env=False)
                    home = str(Path.home())
                    assert home in settings.app_db_url

    def test_default_db_uses_user_data_dir(self, tmp_path: Path):
        """Default DB path should use user data directory."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                with mock.patch("pathlib.Path.mkdir"):
                    settings = load_settings(load_env=False)
                    default_path = get_default_db_path()
                    assert str(default_path) in settings.app_db_url

    def test_invalid_app_env_defaults_to_local(self, tmp_path: Path):
        """Invalid APP_ENV should default to local."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env["APP_ENV"] = "invalid"
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                assert settings.app_env == "local"

    def test_mode_aliases(self, tmp_path: Path):
        """Various mode aliases should be handled correctly."""
        from api.config import load_settings

        test_cases = [
            ("local", "local-only"),
            ("local-only", "local-only"),
            ("hybrid", "hybrid"),
            ("cloud", "cloud-enabled"),
            ("cloud-enabled", "cloud-enabled"),
            ("invalid", "local-only"),
        ]

        nonexistent_config = tmp_path / "nope.toml"
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            for input_val, expected in test_cases:
                base_env = preserve_home_env()
                base_env["APP_DEFAULT_MODE"] = input_val
                with mock.patch.dict(os.environ, base_env, clear=True):
                    settings = load_settings(load_env=False)
                    assert settings.app_default_mode == expected


class TestSettings:
    """Tests for Settings dataclass."""

    def test_reload_enabled_in_local_env(self, tmp_path: Path):
        """reload_enabled should be True in local env."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env["APP_ENV"] = "local"
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                assert settings.reload_enabled is True

    def test_reload_disabled_in_prod(self, tmp_path: Path):
        """reload_enabled should be False in prod env."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env["APP_ENV"] = "prod"
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                assert settings.reload_enabled is False

    def test_uppercase_aliases(self, tmp_path: Path):
        """Uppercase aliases should return same values."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env.update({
            "APP_ENV": "dev",
            "APP_HOST": "localhost",
            "APP_PORT": "9000",
            "APP_DEFAULT_MODE": "hybrid",
        })
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                assert settings.APP_ENV == settings.app_env
                assert settings.APP_HOST == settings.app_host
                assert settings.APP_PORT == settings.app_port
                assert settings.APP_DEFAULT_MODE == settings.app_default_mode

    def test_to_dict_structure(self, tmp_path: Path):
        """to_dict should return structured config."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                config_dict = settings.to_dict()
                assert "core" in config_dict
                assert "storage" in config_dict
                assert "llm" in config_dict
                assert "search" in config_dict

    def test_to_dict_redacts_secrets(self, tmp_path: Path):
        """to_dict should redact sensitive values."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env.update({
            "LLM_API_KEY": "sk-1234567890abcdef",
            "SEARCH_API_KEY": "search-key-123",
        })
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                config_dict = settings.to_dict(redact_secrets=True)
                # Redacted format: first4...last4
                assert "..." in config_dict["llm"]["api_key"]
                assert config_dict["llm"]["api_key"] != "sk-1234567890abcdef"
                assert "..." in config_dict["search"]["api_key"]
                assert config_dict["search"]["api_key"] != "search-key-123"

    def test_to_dict_shows_secrets_when_requested(self, tmp_path: Path):
        """to_dict should show secrets when redact_secrets=False."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env["LLM_API_KEY"] = "sk-1234567890abcdef"
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                config_dict = settings.to_dict(redact_secrets=False)
                assert config_dict["llm"]["api_key"] == "sk-1234567890abcdef"


class TestResolveDbUrl:
    """Tests for _resolve_db_url helper."""

    def test_preserves_memory_db(self):
        """Should preserve :memory: database URL."""
        from api.config import _resolve_db_url

        result = _resolve_db_url("sqlite:///:memory:")
        assert result == "sqlite:///:memory:"

    def test_expands_relative_path(self, tmp_path: Path):
        """Should expand relative paths to absolute."""
        from api.config import _resolve_db_url

        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = _resolve_db_url("sqlite:///test.db")
            assert result.startswith("sqlite:///")
            assert "/test.db" in result or "\\test.db" in result
        finally:
            os.chdir(original_cwd)

    def test_preserves_absolute_path(self):
        """Should preserve absolute paths."""
        from api.config import _resolve_db_url

        result = _resolve_db_url("sqlite:////absolute/path/to/db.sqlite3")
        assert result == "sqlite:////absolute/path/to/db.sqlite3"


class TestSearchApiKeyResolution:
    """Tests for search API key resolution."""

    def test_builtin_provider_empty_key(self, tmp_path: Path):
        """Builtin provider should return empty key."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env["SEARCH_PROVIDER"] = "builtin"
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                assert settings.get_effective_search_api_key() == ""

    def test_tavily_key_from_env(self, tmp_path: Path):
        """Should get Tavily key from TAVILY_API_KEY env var."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env.update({
            "SEARCH_PROVIDER": "tavily",
            "TAVILY_API_KEY": "tvly-test123",
        })
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                assert settings.get_effective_search_api_key() == "tvly-test123"

    def test_exa_key_from_env(self, tmp_path: Path):
        """Should get Exa key from EXA_API_KEY env var."""
        from api.config import load_settings

        nonexistent_config = tmp_path / "nope.toml"
        base_env = preserve_home_env()
        base_env.update({
            "SEARCH_PROVIDER": "exa",
            "EXA_API_KEY": "exa-test123",
        })
        with mock.patch("aideator.paths.get_default_config_path", return_value=nonexistent_config):
            with mock.patch.dict(os.environ, base_env, clear=True):
                settings = load_settings(load_env=False)
                assert settings.get_effective_search_api_key() == "exa-test123"
