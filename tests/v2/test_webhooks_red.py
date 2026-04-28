from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_webhook_dispatch_red():
    # 1. Setup User and Webhook
    client.post("/api/auth/register", json={"email": "webhook@ex.com", "password": "password"})
    login = client.post(
        "/api/auth/login", data={"username": "webhook@ex.com", "password": "password"}
    )
    token = login.json()["access_token"]

    # Create Webhook (using direct DB since API not yet fully implemented for webhooks)
    from db.base import db_session
    from db.schema import UserModel, WebhookModel

    session = db_session()
    user = session.query(UserModel).filter_by(email="webhook@ex.com").first()
    wh = WebhookModel(
        url="https://example.com/webhook", owner_id=user.user_id, events="run.succeeded"
    )
    session.add(wh)
    session.commit()
    db_session.remove()

    # 2. Trigger a Run and mock the dispatcher to verify call
    # We'll mock the actual HTTP call inside services.webhooks
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Create Idea
        idea_res = client.post(
            "/ideas",
            json={
                "title": "Webhook Test",
                "description": "test",
                "target_user": "test",
                "context": "test",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        idea_id = idea_res.json()["idea_id"]

        # Trigger Run
        # Note: In a real test we'd wait for background task,
        # here we'll call orchestrator directly or assume it runs
        from uuid import UUID

        from db.runs import save_run
        from engine.orchestrator import execute_run
        from models.run import Run

        run = Run(idea_id=UUID(idea_id), tier="low", mode="local-only")
        save_run(run)

        await execute_run(run.run_id)

        # 3. Assert Webhook was called
        assert mock_post.called
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["event"] == "run.succeeded"
        assert kwargs["json"]["payload"]["idea_id"] == idea_id
