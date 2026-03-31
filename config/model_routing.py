"""PH-B model routing and prompt registry helpers."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ALLOWED_MODES = {"local-only", "hybrid", "cloud-enabled"}
ALLOWED_TIERS = {"low", "medium", "high"}
DEFAULT_PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"

Route = dict[str, str]
RoutingConfig = dict[str, dict[str, Route]]

DEFAULT_ROUTING_CONFIG: RoutingConfig = {
    mode: {
        tier: {
            "provider": "litellm",
            "model": f"{tier}-default-model",
            "prompt_id": "analyst",
        }
        for tier in ALLOWED_TIERS
    }
    for mode in ALLOWED_MODES
}


def _load_from_file(config_path: Path) -> RoutingConfig:
    suffix = config_path.suffix.lower()
    payload: Any

    if suffix == ".json":
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - dependency optional
            raise ValueError("YAML routing config requires PyYAML to be installed.") from exc
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Unsupported routing config format: {suffix or '<none>'}")

    if not isinstance(payload, dict):
        raise ValueError("Routing config must be a mapping of mode -> tier -> route.")
    return payload  # type: ignore[return-value]


def validate_model_routing(routing_config: RoutingConfig) -> RoutingConfig:
    """Validate route map shape and known mode/tier keys."""
    if not isinstance(routing_config, dict):
        raise ValueError("Routing config must be a mapping.")

    for mode, tiers in routing_config.items():
        if mode not in ALLOWED_MODES:
            raise ValueError(f"Unknown mode: {mode}")
        if not isinstance(tiers, dict):
            raise ValueError(f"Mode routes must be a mapping: {mode}")

        for tier, route in tiers.items():
            if tier not in ALLOWED_TIERS:
                raise ValueError(f"Unknown tier: {tier}")
            if not isinstance(route, dict):
                raise ValueError(f"Route must be a mapping for {mode}/{tier}")

            model = route.get("model")
            prompt_id = route.get("prompt_id")
            if not isinstance(model, str) or not model.strip():
                raise ValueError(f"Missing model for {mode}/{tier}")
            if not isinstance(prompt_id, str) or not prompt_id.strip():
                raise ValueError(f"Missing prompt_id for {mode}/{tier}")

    return routing_config


def load_prompt_registry(prompt_dir: Path | None = None) -> dict[str, str]:
    """Load prompt id -> file path registry from prompt directory."""
    base = prompt_dir or DEFAULT_PROMPT_DIR
    if not base.exists():
        raise ValueError(f"Prompt directory does not exist: {base}")

    registry = {path.stem: str(path) for path in base.glob("*.txt")}
    if not registry:
        raise ValueError("Prompt directory contains no .txt prompt files.")
    return registry


def validate_prompt_registry(
    routing_config: RoutingConfig,
    prompt_registry: dict[str, str],
) -> dict[str, str]:
    """Ensure all configured prompt ids resolve to existing files."""
    for mode_routes in routing_config.values():
        for route in mode_routes.values():
            prompt_id = route["prompt_id"]
            prompt_path = prompt_registry.get(prompt_id)
            if prompt_path is None:
                raise ValueError(f"Prompt id not found in registry: {prompt_id}")
            if not Path(prompt_path).exists():
                raise ValueError(f"Prompt file does not exist: {prompt_path}")
    return prompt_registry


def load_routing_config(
    config_path: Path | str | None = None,
    prompt_dir: Path | None = None,
) -> RoutingConfig:
    """Load and validate routing config and prompt registry."""
    if config_path is None:
        routing_config = deepcopy(DEFAULT_ROUTING_CONFIG)
    else:
        path = Path(config_path)
        routing_config = _load_from_file(path)

    validated = validate_model_routing(routing_config)
    prompt_registry = load_prompt_registry(prompt_dir=prompt_dir)
    validate_prompt_registry(validated, prompt_registry)
    return validated


def resolve_route(
    mode: str,
    tier: str,
    routing_config: RoutingConfig | None = None,
) -> Route:
    """Resolve route for a mode/tier pair."""
    if mode not in ALLOWED_MODES:
        raise ValueError(f"Unknown mode: {mode}")
    if tier not in ALLOWED_TIERS:
        raise ValueError(f"Unknown tier: {tier}")

    config = routing_config or load_routing_config()
    validated = validate_model_routing(config)
    try:
        return validated[mode][tier]
    except KeyError as exc:
        raise ValueError(f"No route configured for {mode}/{tier}") from exc


def get_route_for_mode_tier(
    mode: str,
    tier: str,
    routing_config: RoutingConfig | None = None,
) -> Route:
    """Alias for resolve_route for compatibility."""
    return resolve_route(mode=mode, tier=tier, routing_config=routing_config)
