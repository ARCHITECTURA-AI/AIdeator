"""CLI command package scaffold.

This package name shadows Python's stdlib ``cmd`` module in test/runtime import
paths. Expose ``Cmd`` from stdlib semantics so ``import pdb`` (used by pytest)
can still resolve ``cmd.Cmd``.
"""

from __future__ import annotations

import sysconfig
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType


def _load_stdlib_cmd_module() -> ModuleType | None:
    stdlib_dir = sysconfig.get_paths().get("stdlib")
    if not stdlib_dir:
        return None
    cmd_file = Path(stdlib_dir) / "cmd.py"
    if not cmd_file.exists():
        return None
    spec = spec_from_file_location("_stdlib_cmd", cmd_file)
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_stdlib_cmd = _load_stdlib_cmd_module()

if _stdlib_cmd is not None and hasattr(_stdlib_cmd, "Cmd"):
    Cmd = _stdlib_cmd.Cmd
else:
    class _FallbackCmd:  # pragma: no cover - fallback for unusual runtimes
        """Minimal fallback for environments without a loadable stdlib cmd."""

        prompt = ""

    Cmd = _FallbackCmd

