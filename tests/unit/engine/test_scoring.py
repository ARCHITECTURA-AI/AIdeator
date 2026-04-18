"""Unit tests for V1 scoring system."""

from __future__ import annotations

import pytest

from engine.synthesizer import (
    normalize_score,
    score_to_band,
    synthesize_default_cards,
    validate_cards,
    validate_cards_v1,
)
from models.report import Card


class TestScoreToBand:
    """Tests for score-to-band mapping."""

    def test_high_band(self) -> None:
        assert score_to_band(70) == "high"
        assert score_to_band(85) == "high"
        assert score_to_band(100) == "high"

    def test_medium_band(self) -> None:
        assert score_to_band(40) == "medium"
        assert score_to_band(55) == "medium"
        assert score_to_band(69) == "medium"

    def test_low_band(self) -> None:
        assert score_to_band(0) == "low"
        assert score_to_band(20) == "low"
        assert score_to_band(39) == "low"

    def test_boundary_70(self) -> None:
        assert score_to_band(70) == "high"
        assert score_to_band(69) == "medium"

    def test_boundary_40(self) -> None:
        assert score_to_band(40) == "medium"
        assert score_to_band(39) == "low"


class TestNormalizeScore:
    """Tests for score normalization."""

    def test_legacy_float_to_int(self) -> None:
        assert normalize_score(0.62) == 62
        assert normalize_score(0.0) == 0
        assert normalize_score(1.0) == 100

    def test_already_int(self) -> None:
        assert normalize_score(75) == 75
        assert normalize_score(0) == 0
        assert normalize_score(100) == 100

    def test_clamp_high(self) -> None:
        assert normalize_score(150) == 100

    def test_clamp_low(self) -> None:
        assert normalize_score(-10) == 0




class TestValidateCardsV1:
    """Tests for V1 card validation with scores and bands."""

    def test_valid_cards(self) -> None:
        cards = synthesize_default_cards()
        validate_cards_v1(cards)  # Should not raise

    def test_score_in_range(self) -> None:
        cards = synthesize_default_cards()
        for card in cards:
            score = card.score
            if score is not None:
                assert 0 <= int(score) <= 100

    def test_band_matches_score(self) -> None:
        cards = synthesize_default_cards()
        for card in cards:
            score = card.score
            band = card.meta.get("band")
            expected = score_to_band(normalize_score(score))
            err_msg = f"{card.type}: score={score} -> expected {expected}, got {band}"
            assert band == expected, err_msg

    def test_invalid_band_raises(self) -> None:
        cards = [
            Card(
                type="demand", title="T", summary="s", score=50,
                meta={"band": "extreme", "citation_urls": ["u"]}
            ),
            Card(
                type="competition", title="T", summary="s", score=50,
                meta={"band": "medium", "citation_urls": ["u"]}
            ),
            Card(
                type="viability", title="T", summary="s", score=50,
                meta={"band": "medium", "citation_urls": ["u"]}
            ),
            Card(
                type="next_steps", title="T", summary="s", score=50,
                meta={"band": "medium", "citation_urls": []}
            ),
        ]
        with pytest.raises(ValueError, match="Invalid band"):
            validate_cards_v1(cards)

    def test_mismatched_band_raises(self) -> None:
        cards = [
            Card(
                type="demand", title="T", summary="s", score=80,
                meta={"band": "low", "citation_urls": ["u"]}
            ),
            Card(
                type="competition", title="T", summary="s", score=50,
                meta={"band": "medium", "citation_urls": ["u"]}
            ),
            Card(
                type="viability", title="T", summary="s", score=50,
                meta={"band": "medium", "citation_urls": ["u"]}
            ),
            Card(
                type="next_steps", title="T", summary="s", score=50,
                meta={"band": "medium", "citation_urls": []}
            ),
        ]
        with pytest.raises(ValueError, match="Band mismatch"):
            validate_cards_v1(cards)


class TestSynthesizeDefaultCards:
    """Tests for default card synthesis."""

    def test_all_required_types_present(self) -> None:
        cards = synthesize_default_cards()
        types = {str(c.type) for c in cards}
        assert types == {"demand", "competition", "viability", "next_steps"}

    def test_all_cards_have_scores(self) -> None:
        cards = synthesize_default_cards()
        for card in cards:
            assert hasattr(card, "score")
            assert "band" in card.meta

    def test_scores_are_integers(self) -> None:
        cards = synthesize_default_cards()
        for card in cards:
            assert isinstance(card.score, int)

    def test_backward_compatible_validation(self) -> None:
        """Legacy validate_cards still works with new format."""
        cards = synthesize_default_cards()
        validate_cards(cards)  # Should not raise
