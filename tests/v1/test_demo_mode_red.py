import os

import pytest
from fastapi.testclient import TestClient

from api.app import app
from db.ideas import list_ideas
from db.reports import get_report


@pytest.fixture(autouse=True)
def setup_db():
    # Use a test database
    old_url = os.environ.get("APP_DB_URL")
    os.environ["APP_DB_URL"] = "sqlite:///./test_demo.db"
    from db.base import reset_db_connection

    reset_db_connection()
    yield
    if old_url:
        os.environ["APP_DB_URL"] = old_url
    else:
        os.environ.pop("APP_DB_URL", None)
    reset_db_connection()
    if os.path.exists("./test_demo.db"):
        try:
            os.remove("./test_demo.db")
        except Exception:
            pass


def test_demo_mode_creates_data_and_redirects():
    client = TestClient(app)

    # Ensure no ideas exist initially
    ideas = list_ideas()
    assert len(ideas) == 0

    # Hit the demo endpoint
    response = client.get("/demo", follow_redirects=False)

    # Should redirect
    assert response.status_code == 303

    # Check if idea was created
    ideas = list_ideas()
    assert len(ideas) > 0
    demo_idea = ideas[0]
    assert "EcoCharge" in demo_idea.title

    # Check if report was created for the run
    from db.runs import list_runs_for_idea

    runs = list_runs_for_idea(demo_idea.idea_id)
    assert len(runs) > 0
    report = get_report(runs[0].run_id)
    assert report is not None
    assert len(report.cards) > 0

    # Check redirect location
    assert response.headers["location"] == f"/app/runs/{runs[0].run_id}"
