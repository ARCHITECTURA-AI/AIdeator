"""Unit tests for the Validation Stage Gate."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest

from engine.orchestrator import execute_run
from models.idea import Idea, ValidationStatus
from models.report import Card
from models.run import Run


@pytest.mark.asyncio
async def test_stage_gate_graduation() -> None:
    """Test that an idea graduates based on scores."""
    idea_id = uuid4()
    idea = Idea(title="Great Idea", description="Awesome", target_user="Me", context="C")
    idea.idea_id = idea_id
    idea.status = ValidationStatus.DESK_RESEARCH
    
    run_id = uuid4()
    run = Run(run_id=run_id, idea_id=idea_id, tier="high", mode="cloud-enabled")
    
    # Mock dependencies
    mock_analysis = {"demand": 80, "market": 75, "competition": 70, "viability": 85}
    
    mock_cards = [
        Card(score=80, type="demand", title="T", summary="S"),
        Card(score=75, type="market", title="T", summary="S"),
        Card(score=70, type="competition", title="T", summary="S"),
        Card(score=85, type="viability", title="T", summary="S")
    ]
    
    with patch("engine.orchestrator.get_run", return_value=run), \
         patch("engine.orchestrator.transition_run"), \
         patch("engine.orchestrator.get_idea", return_value=idea), \
         patch("engine.orchestrator.collect_search_signals", return_value=[]), \
         patch("engine.orchestrator.analyze_dimensions", return_value=mock_analysis), \
         patch("engine.orchestrator.synthesize_intelligence", return_value=mock_cards), \
         patch("engine.orchestrator.generate_interview_kit", return_value=None), \
         patch("engine.orchestrator.generate_experiment_kit", return_value=None), \
         patch("engine.orchestrator.build_markdown_artifact", return_value=""), \
         patch("engine.orchestrator.save_idea") as mock_save_idea, \
         patch("engine.orchestrator.save_report"), \
         patch("engine.orchestrator.publish_event"):
        
        from engine.battle import BattleOrchestrator
        with patch.object(BattleOrchestrator, "run_battle", return_value={}):
            await execute_run(run_id)
            
    # Should graduate to EXPERIMENT_READY (avg score = 80)
    assert idea.status == ValidationStatus.EXPERIMENT_READY
    mock_save_idea.assert_called_with(idea)

@pytest.mark.asyncio
async def test_stage_gate_pivot() -> None:
    """Test that a poor idea is recommended for a pivot."""
    idea_id = uuid4()
    idea = Idea(title="Bad Idea", description="Terrible", target_user="Nobody", context="C")
    idea.idea_id = idea_id
    
    run_id = uuid4()
    run = Run(run_id=run_id, idea_id=idea_id, tier="high", mode="cloud-enabled")
    
    mock_analysis = {"demand": 20, "market": 10, "competition": 5, "viability": 15}
    
    mock_cards = [
        Card(score=20, type="demand", title="T", summary="S"),
        Card(score=10, type="market", title="T", summary="S"),
        Card(score=5, type="competition", title="T", summary="S"),
        Card(score=15, type="viability", title="T", summary="S")
    ]
    
    with patch("engine.orchestrator.get_run", return_value=run), \
         patch("engine.orchestrator.transition_run"), \
         patch("engine.orchestrator.get_idea", return_value=idea), \
         patch("engine.orchestrator.collect_search_signals", return_value=[]), \
         patch("engine.orchestrator.analyze_dimensions", return_value=mock_analysis), \
         patch("engine.orchestrator.synthesize_intelligence", return_value=mock_cards), \
         patch("engine.orchestrator.generate_interview_kit", return_value=None), \
         patch("engine.orchestrator.generate_experiment_kit", return_value=None), \
         patch("engine.orchestrator.build_markdown_artifact", return_value=""), \
         patch("engine.orchestrator.save_idea"), \
         patch("engine.orchestrator.save_report"), \
         patch("engine.orchestrator.publish_event"):
        
        from engine.battle import BattleOrchestrator
        with patch.object(BattleOrchestrator, "run_battle", return_value={}):
            await execute_run(run_id)
            
    assert idea.status == ValidationStatus.PIVOT_RECOMMENDED
