"""Pytest bootstrap for stable local package resolution."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

existing_config = sys.modules.get("config")
if existing_config is not None and not hasattr(existing_config, "__path__"):
    del sys.modules["config"]
