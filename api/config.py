"""Application configuration loaded from environment variables.

This module centralizes runtime settings for local/dev/prod and mode selection:
- local-only: no outbound HTTP calls allowed by run mode.
- hybrid: curated external signal fetches with keyword-only payloads.
- cloud-enabled: full external mode.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

AppEnv = Literal["local", "dev", "prod"]
RunMode = Literal["local-only", "hybrid", "cloud-enabled"]
DefaultModeEnv = Literal["local", "hybrid", "cloud"]


def _load_dotenv(path: Path) -> None:
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
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_mode_from_env(raw: str) -> RunMode:
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


@dataclass(frozen=True)
class Settings:
    app_env: AppEnv
    app_host: str
    app_port: int
    app_db_url: str
    app_docs_dir: Path
    app_default_mode: RunMode

    tavily_api_key: str
    reddit_client_id: str
    reddit_client_secret: str
    llm_api_base: str
    llm_api_key: str

    log_level: str
    log_json: bool

    @property
    def reload_enabled(self) -> bool:
        return self.app_env == "local"

    # Compatibility aliases for call sites that prefer upper-case setting names.
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


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[1]
    _load_dotenv(project_root / ".env")

    app_env = os.getenv("APP_ENV", "local").strip().lower()
    if app_env not in {"local", "dev", "prod"}:
        app_env = "local"

    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = int(os.getenv("APP_PORT", "8000"))
    app_db_url = os.getenv("APP_DB_URL", "sqlite:///./aideator.db")

    docs_raw = os.getenv("APP_DOCS_DIR", "./docs")
    docs_dir = Path(docs_raw)
    app_docs_dir = (project_root / docs_dir).resolve() if not docs_dir.is_absolute() else docs_dir

    default_mode_raw = os.getenv("APP_DEFAULT_MODE", os.getenv("DEFAULT_MODE", "local"))
    app_default_mode = _default_mode_from_env(default_mode_raw)

    return Settings(
        app_env=app_env,  # type: ignore[arg-type]
        app_host=app_host,
        app_port=app_port,
        app_db_url=app_db_url,
        app_docs_dir=app_docs_dir,
        app_default_mode=app_default_mode,
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        llm_api_base=os.getenv("LLM_API_BASE", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        log_json=_parse_bool(os.getenv("LOG_JSON"), default=False),
    )


settings = load_settings()
