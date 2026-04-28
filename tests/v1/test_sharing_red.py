import os

import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.sharing import generate_share_link
from db.base import reset_db_connection
from db.ideas import save_idea
from db.reports import save_report
from db.runs import save_run
from models.idea import Idea
from models.report import Report
from models.run import Run


@pytest.fixture(autouse=True)
def setup_db():
    old_url = os.environ.get("APP_DB_URL")
    os.environ["APP_DB_URL"] = "sqlite:///./test_sharing.db"
    reset_db_connection()
    yield
    if old_url:
        os.environ["APP_DB_URL"] = old_url
    else:
        os.environ.pop("APP_DB_URL", None)
    
    from db.base import engine as current_engine
    current_engine.dispose()
    reset_db_connection()
    if os.path.exists("./test_sharing.db"):
        try:
            os.remove("./test_sharing.db")
        except PermissionError:
            pass
    if os.path.exists("data/shares.json"):
        try:
            os.remove("data/shares.json")
        except PermissionError:
            pass


def test_shared_link_displays_report():
    client = TestClient(app)

    # 1. Create Data
    idea = Idea(title="Shared Idea", description="Desc", target_user="User", context="Ctx")
    save_idea(idea)
    run = Run(idea_id=idea.idea_id, mode="local-only", tier="Bronze", status="succeeded")
    save_run(run)
    report = Report(run_id=run.run_id, cards=[], artifact_path="path", citations=[])
    save_report(report)

    # 2. Generate Share Hash
    share_hash = generate_share_link(idea.idea_id)

    # 3. Hit Public Route
    response = client.get(f"/shared/{share_hash}")

    # Should be successful (once implemented)
    assert response.status_code == 200
    assert "Shared Idea" in response.text
    assert "og:title" in response.text
