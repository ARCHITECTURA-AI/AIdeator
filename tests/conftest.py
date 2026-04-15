"""Test configuration — adds project root to sys.path.

This is needed because the project uses top-level packages
(engine, api, db, etc.) that aren't installed as packages
but are importable from the project root.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path for module imports
_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
