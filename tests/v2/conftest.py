import os

import pytest

from db.base import reset_db_connection


@pytest.fixture(autouse=True)
def db_isolation(request):
    # Use a unique DB for each test file to avoid conflicts
    module_name = request.module.__name__.split(".")[-1]
    db_name = f"test_{module_name}.db"
    
    old_url = os.environ.get("APP_DB_URL")
    os.environ["APP_DB_URL"] = f"sqlite:///./{db_name}"
    os.environ["IDEATOR_STRICT_AUTH"] = "true"
    reset_db_connection()
    
    yield
    
    # Restore environment
    if old_url:
        os.environ["APP_DB_URL"] = old_url
    else:
        os.environ.pop("APP_DB_URL", None)
    
    reset_db_connection()
    
    # Try to delete the test DB
    if os.path.exists(f"./{db_name}"):
        try:
            os.remove(f"./{db_name}")
        except Exception:
            pass
