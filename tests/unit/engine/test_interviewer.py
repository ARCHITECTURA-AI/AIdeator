"""Unit tests for user interview kit generation."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.interviewer import generate_interview_kit
from models.report import InterviewKit


@pytest.mark.asyncio
async def test_generate_interview_kit_basic() -> None:
    """Test that the kit is correctly generated with mock LLM response."""
    analysis = {
        "demand": {"strengths": ["People want this"], "weaknesses": ["Price is high", "Too niche"]},
        "competition": {"strengths": [], "weaknesses": []},
        "viability": {"strengths": [], "weaknesses": []}
    }
    signals = [
        {"source_id": "SRC-001", "type": "pain_complaint", "content": "I hate manually doing X"}
    ]
    
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "script": [
            {"question": "How do you currently solve X?", "rationale": "Identify workaround"}
        ],
        "outreach_templates": {
            "email": "Hi, I am researching X."
        },
        "response_tracker": ["Name", "Problem Intensity"]
    })
    
    mock_provider = MagicMock()
    mock_provider.generate = AsyncMock(return_value=mock_response)
    
    with patch("engine.interviewer.get_provider", return_value=mock_provider):
        kit = await generate_interview_kit(
            title="X Tool",
            description="A tool for X",
            analysis=analysis,
            signals=signals
        )
        
    assert isinstance(kit, InterviewKit)
    assert len(kit.script) == 1
    assert kit.outreach_templates["email"] == "Hi, I am researching X."
    assert "Name" in kit.response_tracker

@pytest.mark.asyncio
async def test_generate_interview_kit_fallback() -> None:
    """Test fallback logic when LLM fails."""
    mock_provider = MagicMock()
    mock_provider.generate = AsyncMock(side_effect=Exception("LLM down"))
    
    with patch("engine.interviewer.get_provider", return_value=mock_provider):
        kit = await generate_interview_kit(
            title="X Tool",
            description="A tool for X",
            analysis={},
            signals=[]
        )
        
    assert isinstance(kit, InterviewKit)
    assert len(kit.script) > 0
    assert "email" in kit.outreach_templates
