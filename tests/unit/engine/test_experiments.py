"""Unit tests for the Experiment Engine."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.experiments import generate_experiment_kit
from models.report import ExperimentKit


@pytest.mark.asyncio
async def test_generate_experiment_kit_success() -> None:
    """Test successful experiment kit generation."""
    mock_response = MagicMock()
    mock_response.content = """
    {
      "hypothesis": "If I launch a landing page, 10 people will sign up.",
      "method": "Smoke Test",
      "landing_page_copy": {
        "headline": "Cool Tool",
        "subheadline": "Does cool things",
        "pain_points": ["Hard", "Slow", "Expensive"],
        "solution": "Easy",
        "cta": "Join"
      },
      "success_metric": "10 signups",
      "tool_stack": ["Carrd", "Tally"]
    }
    """
    
    mock_provider = AsyncMock()
    mock_provider.generate.return_value = mock_response
    
    with patch("engine.experiments.get_provider", return_value=mock_provider):
        kit = await generate_experiment_kit(title="T", description="D")
        
    assert isinstance(kit, ExperimentKit)
    assert kit.hypothesis == "If I launch a landing page, 10 people will sign up."
    assert "Hard\nSlow\nExpensive" in kit.landing_page_copy["pain_points"]
    assert "Carrd" in kit.tool_stack

@pytest.mark.asyncio
async def test_generate_experiment_kit_failure() -> None:
    """Test that failure is raised when LLM fails after retries."""
    mock_provider = AsyncMock()
    mock_provider.generate.side_effect = Exception("LLM Error")
    
    with patch("engine.experiments.get_provider", return_value=mock_provider):
        with pytest.raises(Exception):
            await generate_experiment_kit(title="My Idea", description="Descr")
