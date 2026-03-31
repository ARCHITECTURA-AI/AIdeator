"""Plugin registration and loading contracts for PH-D."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PLUGIN_API_VERSION = "1.0"
REQUIRED_PLUGIN_HOOKS = ("collect_signals",)
OPTIONAL_PLUGIN_HOOKS = ("evaluate_quality",)

_PLUGIN_REGISTRY: dict[str, dict[str, Any]] = {}


@dataclass(frozen=True, slots=True)
class PluginContract:
    plugin_id: str
    api_version: str
    hooks: tuple[str, ...]
    deprecated: tuple[str, ...] = ()


def register_plugin(plugin_id: str, plugin_def: dict[str, Any]) -> PluginContract:
    """Register plugin metadata under a stable API contract."""
    api_version = str(plugin_def.get("api_version", PLUGIN_API_VERSION))
    hooks = tuple(str(hook) for hook in plugin_def.get("hooks", REQUIRED_PLUGIN_HOOKS))
    _PLUGIN_REGISTRY[plugin_id] = {"api_version": api_version, "hooks": hooks}
    return PluginContract(plugin_id=plugin_id, api_version=api_version, hooks=hooks)


def load_plugins() -> list[PluginContract]:
    """Load all registered plugins in a deterministic order."""
    contracts: list[PluginContract] = []
    for plugin_id in sorted(_PLUGIN_REGISTRY):
        definition = _PLUGIN_REGISTRY[plugin_id]
        contracts.append(
            PluginContract(
                plugin_id=plugin_id,
                api_version=str(definition.get("api_version", PLUGIN_API_VERSION)),
                hooks=tuple(str(hook) for hook in definition.get("hooks", ())),
            )
        )
    return contracts
