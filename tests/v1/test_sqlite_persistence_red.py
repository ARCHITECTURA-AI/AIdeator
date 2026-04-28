import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

from db.ideas import get_idea, initialize, list_ideas, save_idea
from models.idea import Idea


@pytest.fixture(autouse=True)
def setup_teardown(monkeypatch):
    """Isolate persistence tests using a unique file in a temp directory."""
    import tempfile
    import uuid

    from db import base
    
    # Create a temp directory for this test
    temp_dir = Path(tempfile.mkdtemp())
    test_file = f"aideator_test_{uuid.uuid4().hex}.db"
    test_path = (temp_dir / test_file).absolute()
    
    # Monkeypatch the DB_DIR and DB_PATH in db.base
    monkeypatch.setattr(base, "DB_DIR", temp_dir)
    monkeypatch.setattr(base, "DB_PATH", test_path)
    
    # Ensure APP_DB_URL is NOT set so it uses the default logic we just patched
    monkeypatch.delenv("APP_DB_URL", raising=False)
    
    from db.base import reset_db_connection
    reset_db_connection()

    yield test_path

    # Cleanup
    from db.base import db_session, engine
    db_session.remove()
    engine.dispose()

    if test_path.exists():
        try:
            os.remove(test_path)
        except Exception:
            pass


def test_sqlite_db_file_created(setup_teardown):
    """Verify that a SQLite database file is created in data/ directory."""
    test_path = setup_teardown
    initialize()
    idea = Idea(
        title="Test Idea",
        description="A test description",
        target_user="Test User",
        context="Test Context",
    )
    save_idea(idea)

    assert test_path.exists(), f"SQLite database file should be created at {test_path}"


def test_idea_persistence_integrity():
    """Verify that ideas saved to SQLite can be retrieved with full integrity."""
    initialize()
    idea = Idea(
        title="Persistence Test",
        description="Checking data types",
        target_user="Power Users",
        context="Local testing",
        tier="Gold",
        brand_hex="#FF0080",
    )
    saved = save_idea(idea)

    retrieved = get_idea(saved.idea_id)
    assert retrieved is not None
    assert retrieved.title == "Persistence Test"
    assert retrieved.tier == "Gold"
    assert retrieved.brand_hex == "#FF0080"
    assert isinstance(retrieved.created_at, datetime)


def test_list_ideas_from_sqlite():
    """Verify listing ideas from the SQLite database."""
    initialize()
    # Clear existing if any (fixtures should handle, but let's be safe)
    ideas = [
        Idea(title=f"Idea {i}", description="Desc", target_user="User", context="Ctx")
        for i in range(3)
    ]
    for idea in ideas:
        save_idea(idea)

    all_ideas = list_ideas()
    assert len(all_ideas) >= 3
    titles = [i.title for i in all_ideas]
    for i in range(3):
        assert f"Idea {i}" in titles


def test_run_persistence():
    """Verify run persistence in SQLite."""
    from db.runs import get_run, save_run
    from models.run import Run

    initialize()
    idea_id = uuid4()
    run = Run(idea_id=idea_id, tier="low", mode="local-only")
    save_run(run)

    retrieved = get_run(run.run_id)
    assert retrieved is not None
    assert retrieved.idea_id == idea_id
    assert retrieved.status == "pending"


def test_report_persistence():
    """Verify report persistence in SQLite."""
    from db.reports import get_report, save_report
    from models.report import Card, Report

    initialize()
    run_id = uuid4()
    report = Report(
        run_id=run_id,
        cards=[Card(type="market", title="Market", summary="Big", score=80)],
        artifact_path="path/to/art",
        citations=[],
    )
    save_report(report)

    retrieved = get_report(run_id)
    assert retrieved is not None
    assert len(retrieved.cards) == 1
    assert retrieved.cards[0].title == "Market"


def test_signal_persistence():
    """Verify signal persistence in SQLite."""
    from db.signals import list_signals, save_signal

    initialize()
    run_id = uuid4()
    save_signal(run_id, {"key": "val"})
    save_signal(run_id, {"key2": "val2"})

    signals = list_signals(run_id)
    assert len(signals) == 2
    assert signals[0]["key"] == "val"


def test_comment_persistence():
    """Verify comment persistence in SQLite."""
    from db.comments import add_comment, list_comments_for_idea
    from models.comment import Comment

    initialize()
    idea_id = uuid4()
    comment = Comment(idea_id=idea_id, author="User", content="Nice!")
    add_comment(comment)

    comments = list_comments_for_idea(idea_id)
    assert len(comments) == 1
    assert comments[0].content == "Nice!"
