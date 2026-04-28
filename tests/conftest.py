"""Test configuration — adds project root to sys.path.

This is needed because the project uses top-level packages
(engine, api, db, etc.) that aren't installed as packages
but are importable from the project root.
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for module imports
_ROOT = str(Path(__file__).resolve().parents[1])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.environ["IDEATOR_TEST_BYPASS"] = "true"
os.environ["APP_DB_URL"] = "sqlite:///./test_aideator_global.db"

import pytest  # noqa: E402

from db.base import reset_db_connection  # noqa: E402


@pytest.fixture(autouse=True)
def db_init():
    """Ensure database is initialized for every test."""
    reset_db_connection()
    yield
    # Cleanup after all tests if needed
