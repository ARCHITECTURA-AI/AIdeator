from uuid import uuid4

import pytest
from pydantic import ValidationError

from models.report import Card, Report


def test_card_validation():
    # Valid card
    card = Card(
        title="Market Demand",
        summary="High demand",
        description="Detailed description",
        score=85,
        type="demand",
        meta={"band": "strong"}
    )
    assert card.title == "Market Demand"
    assert card.score == 85

def test_card_invalid_score():
    with pytest.raises(ValidationError):
        Card(
            title="Too High",
            summary="Invalid",
            description="Score > 100",
            score=150,
            type="demand"
        )

def test_report_validation():
    run_id = uuid4()
    card = Card(
        title="Test",
        summary="Test",
        description="Test",
        score=50,
        type="viability"
    )
    report = Report(
        run_id=run_id,
        cards=[card],
        artifact_path="docs/test.md"
    )
    assert report.run_id == run_id
    assert len(report.cards) == 1
    assert report.cards[0].title == "Test"

def test_report_serialization():
    run_id = uuid4()
    card = Card(title="X", summary="Y", description="Z", score=10, type="demand")
    report = Report(run_id=run_id, cards=[card], artifact_path="p")
    
    data = report.model_dump()
    assert str(data["run_id"]) == str(run_id)
    assert data["cards"][0]["score"] == 10
    
    restored = Report.model_validate(data)
    assert restored.run_id == run_id
    assert restored.cards[0].score == 10
