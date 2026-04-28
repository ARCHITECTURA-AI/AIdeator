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
def db_init(monkeypatch):
    """Ensure database is initialized for every test with a unique file in temp dir."""
    import tempfile
    import uuid
    
    # Use system temp dir to avoid OneDrive locks and slowness
    temp_dir = tempfile.gettempdir()
    test_db_file = os.path.join(temp_dir, f"test_aideator_{uuid.uuid4().hex}.db")
    test_db_url = f"sqlite:///{test_db_file}"
    
    # Use monkeypatch to isolate the environment change to this test
    monkeypatch.setenv("APP_DB_URL", test_db_url)
    
    reset_db_connection()
    
    yield
    
    # Cleanup: Close connections and remove the test file
    from db.base import db_session, engine
    db_session.remove()
    engine.dispose()
    
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass
