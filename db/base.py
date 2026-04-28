"""Thread-safe SQLite storage base."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Ensure data directory exists
DB_DIR = Path("data")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = (DB_DIR / "aideator.db").absolute()


def _get_engine():
    url = os.getenv("APP_DB_URL", f"sqlite:///{DB_PATH}")
    kwargs = {}
    if not url.startswith("sqlite"):
        kwargs["pool_size"] = 20
        kwargs["max_overflow"] = 10

    return create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
        pool_pre_ping=True,
        **kwargs,
    )


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)


def reset_db_connection():
    """Reset the engine and session (useful for tests)."""
    global engine, SessionLocal
    engine.dispose()
    engine = _get_engine()
    SessionLocal.configure(bind=engine)
    db_session.remove()
    initialize_db()


def initialize_db():
    """Create all tables defined in schema.py."""
    from db.schema import Base

    Base.metadata.create_all(bind=engine)
    logging.getLogger("db.base").info(f"Initialized SQLite database at {DB_PATH}")


# Keep the BaseJsonStorage class for backward compatibility during migration if needed,
# but it will be deprecated.
class BaseJsonStorage:
    """DEPRECATED: Use db_session instead."""

    def __init__(self, *args, **kwargs):
        pass

    def load(self, *args, **kwargs):
        pass

    def flush(self, *args, **kwargs):
        pass
