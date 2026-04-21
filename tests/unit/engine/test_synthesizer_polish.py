import pytest
from engine.synthesizer import render_markdown_report
from models.report import Card

def test_render_markdown_polish_hooks():
    """TC-W-001: Verify that the synthesizer includes animation hooks in the output."""
    cards = [
        Card(
            type="demand",
            title="Market Demand",
            score=85,
            summary="High demand detected.",
            details=["Finding 1"],
            meta={"citations": ["http://example.com"]}
        )
    ]
    
    # Matching actual signature: idea_id: str, cards: list[Card]
    markdown = render_markdown_report(idea_id="test-id", cards=cards)
    
    # Check for reveal wrapper
    assert '<div class="reveal">' in markdown
    assert '</div> <!-- end reveal -->' in markdown
    
    # Check for score animation hook
    assert 'class="score-display animate-score"' in markdown
    assert 'data-target="85"' in markdown
    assert '>0</span>' in markdown
