"""Application configuration loaded from environment and config files.

This module centralizes runtime settings for local/dev/prod and mode selection:
- local-only: no outbound HTTP calls allowed by run mode.
- hybrid: curated external signal fetches with keyword-only payloads.
- cloud-enabled: full external mode.

Priority order (highest to lowest):
1. CLI arguments (passed at runtime)
2. Environment variables
3. Config file (aideator.toml)
4. Default values
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import toml  # type: ignore[import-untyped]

from aideator.paths import (
    ensure_dir,
    get_default_config_path,
    get_default_db_path,
    get_default_docs_dir,
    resolve_path,
)

AppEnv = Literal["local", "dev", "prod"]
RunMode = Literal["local-only", "hybrid", "cloud-enabled"]
DefaultModeEnv = Literal["local", "hybrid", "cloud"]

# Config file schema sections
CONFIG_SECTIONS = {"core", "storage", "llm", "search"}


def _load_dotenv(path: Path) -> None:
    """Load environment variables from .env file."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    """Parse a string value as boolean."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_mode_from_env(raw: str) -> RunMode:
    """Convert environment string to RunMode."""
    normalized = raw.strip().lower()
    mapping: dict[str, RunMode] = {
        "local": "local-only",
        "local-only": "local-only",
        "hybrid": "hybrid",
        "cloud": "cloud-enabled",
        "cloud-enabled": "cloud-enabled",
    }
    mode = mapping.get(normalized)
    if mode is None:
        return "local-only"
    return mode


def _resolve_db_url(db_url: str) -> str:
    """Resolve database URL, converting relative paths to absolute."""
    if db_url.startswith("sqlite:///"):
        # Extract the path part
        path_part = db_url[10:]  # After "sqlite:///"
        if not path_part.startswith("/") and not path_part.startswith("~"):
            # Relative path - resolve against project root or use as-is for memory
            if path_part == ":memory:":
                return db_url
            resolved = resolve_path(path_part)
            return f"sqlite:///{resolved}"
        elif path_part.startswith("~"):
            resolved = resolve_path(path_part)
            return f"sqlite:///{resolved}"
    return db_url


def _redact_sensitive(value: str, visible_chars: int = 4) -> str:
    """Redact sensitive values, showing only first/last few characters."""
    if not value or len(value) <= visible_chars * 2:
        return "***"
    return f"{value[:visible_chars]}...{value[-visible_chars:]}"


def load_config_file(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from TOML file.

    Args:
        config_path: Path to config file. If None, uses default location.

    Returns:
        Dictionary containing config values.
    """
    if config_path is None:
        config_path = get_default_config_path()

    if not config_path.exists():
        return {}

    try:
        with open(config_path, encoding="utf-8") as f:
            config = toml.load(f)
        return config
    except Exception:
        # If config file is malformed, return empty dict
        return {}


@dataclass(frozen=True)
class Settings:
    """Application settings container.

    Settings are loaded with priority:
    CLI args > Environment vars > Config file > Defaults
    """

    # Core settings
    app_env: AppEnv
    app_host: str
    app_port: int
    app_db_url: str
    app_docs_dir: Path
    app_default_mode: RunMode

    # External service credentials
    tavily_api_key: str
    reddit_client_id: str
    reddit_client_secret: str

    # LLM settings
    llm_provider: str  # ollama, openai-compatible, anthropic-compatible, mistral-compatible
    llm_model: str
    llm_api_base: str
    llm_api_key: str

    # Search settings
    search_provider: str  # duckduckgo, tavily, exa, searxng, builtin
    search_api_key: str  # Fallback key for search providers
    tavily_api_key_env: str  # Environment variable name for Tavily key
    exa_api_key_env: str  # Environment variable name for Exa key
    searxng_instance_url: str  # SearXNG instance URL (for searxng provider)

    # Logging settings
    log_level: str
    log_json: bool

    # Config source tracking
    _config_source: str = field(default="env", repr=False)

    @property
    def reload_enabled(self) -> bool:
        """Whether auto-reload is enabled (only in local env)."""
        return self.app_env == "local"

    # Compatibility aliases for call sites that prefer upper-case setting names
    @property
    def APP_ENV(self) -> AppEnv:
        return self.app_env

    @property
    def APP_HOST(self) -> str:
        return self.app_host

    @property
    def APP_PORT(self) -> int:
        return self.app_port

    @property
    def APP_DB_URL(self) -> str:
        return self.app_db_url

    @property
    def APP_DOCS_DIR(self) -> Path:
        return self.app_docs_dir

    @property
    def APP_DEFAULT_MODE(self) -> RunMode:
        return self.app_default_mode

    def to_dict(self, redact_secrets: bool = True) -> dict[str, Any]:
        """Convert settings to dictionary.

        Args:
            redact_secrets: If True, redact sensitive values.

        Returns:
            Dictionary of settings.
        """
        result = {
            "core": {
                "app_env": self.app_env,
                "app_host": self.app_host,
                "app_port": self.app_port,
                "default_mode": self.app_default_mode,
            },
            "storage": {
                "db_url": self.app_db_url,
                "docs_dir": str(self.app_docs_dir),
            },
            "llm": {
                "provider": self.llm_provider,
                "model": self.llm_model,
                "api_base": self.llm_api_base,
                "api_key": (
                    _redact_sensitive(self.llm_api_key) if redact_secrets else self.llm_api_key
                ),
            },
            "search": {
                "provider": self.search_provider,
                "api_key": (
                    _redact_sensitive(self.search_api_key)
                    if redact_secrets
                    else self.search_api_key
                ),
                "tavily_api_key_env": self.tavily_api_key_env,
                "exa_api_key_env": self.exa_api_key_env,
                "searxng_instance_url": self.searxng_instance_url,
            },
        }
        return result

    def get_effective_search_api_key(self) -> str:
        """Get the effective search API key based on provider."""
        if self.search_provider == "tavily":
            env_var = self.tavily_api_key_env or "TAVILY_API_KEY"
            return os.getenv(env_var, self.search_api_key or self.tavily_api_key)
        elif self.search_provider == "exa":
            env_var = self.exa_api_key_env or "EXA_API_KEY"
            return os.getenv(env_var, self.search_api_key)
        return ""


def load_settings(
    *,
    cli_db_url: str | None = None,
    cli_docs_dir: str | None = None,
    cli_config_path: Path | None = None,
    load_env: bool = True,
) -> Settings:
    """Load application settings from all sources.

    Priority order (highest to lowest):
    1. CLI arguments (cli_* parameters)
    2. Environment variables
    3. Config file (aideator.toml)
    4. Default values

    Args:
        cli_db_url: Database URL from CLI --db flag
        cli_docs_dir: Docs directory from CLI --docs flag
        cli_config_path: Config file path from CLI --config flag

    Returns:
        Settings object with all configuration values.
    """
    project_root = Path(__file__).resolve().parents[1]
    if load_env:
        _load_dotenv(project_root / ".env")

    # Load config file (lowest priority after defaults)
    config_path = cli_config_path or get_default_config_path()
    file_config = load_config_file(config_path)

    core_config = file_config.get("core", {})
    storage_config = file_config.get("storage", {})
    llm_config = file_config.get("llm", {})
    search_config = file_config.get("search", {})

    # Core settings
    app_env = os.getenv("APP_ENV", core_config.get("app_env", "local")).strip().lower()
    if app_env not in {"local", "dev", "prod"}:
        app_env = "local"

    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = int(os.getenv("APP_PORT", "8000"))

    # Determine default DB and docs paths
    default_db_path = get_default_db_path()
    default_docs_dir = get_default_docs_dir()

    # DB URL with priority: CLI > Env > Config > Default
    if cli_db_url:
        app_db_url = _resolve_db_url(cli_db_url)
    elif os.getenv("APP_DB_URL"):
        app_db_url = _resolve_db_url(os.getenv("APP_DB_URL", ""))
    elif storage_config.get("db_url"):
        db_url_config = storage_config["db_url"]
        # Expand ~ in config file paths
        if db_url_config.startswith("sqlite:///"):
            path_part = db_url_config[10:]
            if path_part.startswith("~"):
                path_part = str(resolve_path(path_part))
                db_url_config = f"sqlite:///{path_part}"
        app_db_url = db_url_config
    else:
        app_db_url = f"sqlite:///{default_db_path}"

    # Docs directory with priority: CLI > Env > Config > Default
    if cli_docs_dir:
        docs_raw = Path(cli_docs_dir)
        app_docs_dir = docs_raw.resolve() if not docs_raw.is_absolute() else docs_raw
    elif os.getenv("APP_DOCS_DIR"):
        docs_raw = Path(os.getenv("APP_DOCS_DIR", "./docs"))
        app_docs_dir = (
            (project_root / docs_raw).resolve()
            if not docs_raw.is_absolute()
            else docs_raw
        )
    elif storage_config.get("docs_dir"):
        docs_config = storage_config["docs_dir"]
        if docs_config.startswith("~"):
            app_docs_dir = resolve_path(docs_config)
        else:
            docs_path = Path(docs_config)
            app_docs_dir = docs_path.resolve() if not docs_path.is_absolute() else docs_path
    else:
        app_docs_dir = default_docs_dir

    # Ensure docs directory exists
    ensure_dir(app_docs_dir)

    default_mode_raw = os.getenv(
        "APP_DEFAULT_MODE",
        os.getenv("DEFAULT_MODE", core_config.get("default_mode", "local")),
    )
    app_default_mode = _default_mode_from_env(default_mode_raw)

    # LLM settings
    llm_provider = os.getenv(
        "LLM_PROVIDER", llm_config.get("provider", "ollama")
    ).strip().lower()
    llm_model = os.getenv("LLM_MODEL", llm_config.get("model", "mistral:7b"))
    llm_api_base = os.getenv(
        "LLM_API_BASE", llm_config.get("api_base", "http://localhost:11434")
    )

    # Get LLM API key (check env var from config first, then direct env)
    llm_api_key_env = llm_config.get("api_key_env", "LLM_API_KEY")
    llm_api_key = os.getenv(llm_api_key_env, os.getenv("LLM_API_KEY", ""))

    # Search settings
    search_provider = os.getenv(
        "SEARCH_PROVIDER", search_config.get("provider", "duckduckgo")
    ).strip().lower()
    search_api_key = os.getenv("SEARCH_API_KEY", "")

    tavily_api_key_env = search_config.get("tavily_api_key_env", "TAVILY_API_KEY")
    exa_api_key_env = search_config.get("exa_api_key_env", "EXA_API_KEY")
    searxng_instance_url = os.getenv(
        "SEARXNG_URL", search_config.get("searxng_instance_url", "http://localhost:8888")
    )

    # Load Tavily key from configured env var or fallback
    tavily_api_key = os.getenv(tavily_api_key_env, os.getenv("TAVILY_API_KEY", ""))

    return Settings(
        app_env=app_env,  # type: ignore[arg-type]
        app_host=app_host,
        app_port=app_port,
        app_db_url=app_db_url,
        app_docs_dir=app_docs_dir,
        app_default_mode=app_default_mode,
        tavily_api_key=tavily_api_key,
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_base=llm_api_base,
        llm_api_key=llm_api_key,
        search_provider=search_provider,
        search_api_key=search_api_key,
        tavily_api_key_env=tavily_api_key_env,
        exa_api_key_env=exa_api_key_env,
        searxng_instance_url=searxng_instance_url,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        log_json=_parse_bool(os.getenv("LOG_JSON"), default=False),
        _config_source=str(config_path) if config_path.exists() else "env",
    )


# Global settings instance (loaded at import time)
settings = load_settings()
