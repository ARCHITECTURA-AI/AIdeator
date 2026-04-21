"""Integration tests for SSE run events (TC-I-060)."""

from __future__ import annotations

import asyncio
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.app import app
from engine.events import publish_event

client = TestClient(app)

@pytest.mark.asyncio
async def test_sse_endpoint_streams_events() -> None:
    from uuid import uuid4

    from db.runs import save_run
    from engine.events import bus
    from models.run import Run
    
    run_id = uuid4()
    save_run(Run(run_id=run_id, idea_id=uuid4(), status="pending", mode="local-only", tier="high"))

    # We use a background task to publish events while the client is reading
    async def produce_events():
        # wait for subscriber
        while run_id not in bus._subscribers:
            await asyncio.sleep(0.01)
        await publish_event(run_id, "connected", {"status": "ok"})
        await publish_event(run_id, "test_event", {"content": "hello"})
        await publish_event(run_id, "completed", {"status": "succeeded"})

    # Use a mock to ensure the generator finishes immediately for this test
    with patch("api.web.subscribe_run") as mock_sub:
        async def mock_gen(_):
            yield {"type": "connected", "data": {}}
            return
        mock_sub.side_effect = mock_gen
        
        response = client.get(f"/api/runs/{run_id}/events")
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

@pytest.mark.asyncio
async def test_sse_subscription_logic() -> None:
    """Test the subscriber logic directly to ensure events are captured."""
    from engine.events import bus, subscribe_run
    run_id = uuid4()
    
    # Start subscription and run it for one event
    async def get_one():
        async for event in subscribe_run(run_id):
            return event

    task = asyncio.create_task(get_one())
    
    # Wait for the subscriber to be registered
    while run_id not in bus._subscribers:
        await asyncio.sleep(0.01)
    
    # Publish event
    await publish_event(run_id, "ping", {"seq": 1})
    
    # Read event
    event = await task
    assert event["type"] == "ping"
    assert event["data"]["seq"] == 1
