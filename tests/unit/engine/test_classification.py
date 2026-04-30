"""Unit tests for signal classification logic."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aideator.search.providers import SearchResult, SignalType
from engine.signal_collector import classify_signals


@pytest.mark.asyncio
async def test_classify_signals_basic() -> None:
    """Test that signals are correctly classified with mock LLM response."""
    signals = [
        SearchResult(
            title="Reddit Rant", 
            url="https://reddit.com/r/Frustrated", 
            snippet="I hate Jira, it is so slow and complicated."
        ),
        SearchResult(
            title="Market Report", 
            url="https://gartner.com/report", 
            snippet="The project management software market is expected to grow by 10%."
        ),
    ]
    
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "classifications": [
            {"id": 0, "type": "PAIN_COMPLAINT", "confidence": 0.95},
            {"id": 1, "type": "MARKET_DATA", "confidence": 0.70}
        ]
    })
    
    mock_provider = MagicMock()
    mock_provider.generate = AsyncMock(return_value=mock_response)
    
    with patch("engine.signal_collector.get_provider", return_value=mock_provider):
        classified = await classify_signals(signals)
        
    assert len(classified) == 2
    assert classified[0].signal_type == SignalType.PAIN_COMPLAINT
    assert classified[0].confidence == 0.95
    assert classified[1].signal_type == SignalType.MARKET_DATA
    assert classified[1].confidence == 0.70

@pytest.mark.asyncio
async def test_classify_signals_fallback() -> None:
    """Test fallback to generic classification if LLM fails."""
    signals = [
        SearchResult(title="Any result", url="https://example.com", snippet="some content"),
    ]
    
    mock_provider = MagicMock()
    mock_provider.generate = AsyncMock(side_effect=Exception("LLM down"))
    
    with patch("engine.signal_collector.get_provider", return_value=mock_provider):
        classified = await classify_signals(signals)
        
    assert len(classified) == 1
    assert classified[0].signal_type == SignalType.ANECDOTAL_POSITIVE
    assert classified[0].confidence == 0.5
