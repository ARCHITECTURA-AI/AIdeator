"""Unit tests for Orchestrator event broadcasting (TC-U-060)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from engine.orchestrator import execute_run


@pytest.mark.asyncio
async def test_execute_run_broadcasts_events() -> None:
    run_id = uuid4()
    mock_run = MagicMock()
    mock_run.idea_id = uuid4()
    mock_run.mode = "local-only"
    
    # Mocking DB and engine calls
    with patch("engine.orchestrator.get_run", return_value=mock_run), \
         patch("engine.orchestrator.get_idea", return_value=MagicMock()), \
         patch("engine.orchestrator.transition_run"), \
         patch(
             "engine.orchestrator.collect_search_signals",
             new_callable=AsyncMock,
             return_value=[],
         ), \
         patch("engine.orchestrator.analyze_dimensions", new_callable=AsyncMock), \
         patch(
             "engine.orchestrator.synthesize_intelligence",
             new_callable=AsyncMock,
             return_value=[],
         ), \
         patch("engine.orchestrator.save_report"), \
         patch("engine.orchestrator.settings"), \
         patch("pathlib.Path.write_text"), \
         patch("engine.orchestrator.build_markdown_artifact"), \
         patch("engine.orchestrator.publish_event", new_callable=AsyncMock) as mock_publish:
        
        await execute_run(run_id)
        
        # Verify that major stages emitted events
        # We expect at least: collecting_signals, analyzing, synthesizing, completed
        emitted_types = [call.args[1] for call in mock_publish.call_args_list]
        
        assert "collecting_signals" in emitted_types
        assert "analyzing" in emitted_types
        assert "synthesizing" in emitted_types
        assert "completed" in emitted_types
