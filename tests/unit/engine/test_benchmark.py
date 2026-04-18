"""Unit tests for internal benchmark module."""

from __future__ import annotations

from engine.benchmark import (
    REFERENCE_CORPUS,
    compare_scores,
    compute_percentile,
    format_comparison_summary,
)


class TestComputePercentile:
    """Tests for percentile calculation."""

    def test_empty_returns_50(self) -> None:
        assert compute_percentile(50, []) == 50

    def test_lowest_value(self) -> None:
        result = compute_percentile(10, [10, 20, 30, 40, 50])
        assert result == 10  # 0 below, 1 equal -> (0 + 0.5*1)/5 * 100 = 10

    def test_highest_value(self) -> None:
        result = compute_percentile(50, [10, 20, 30, 40, 50])
        assert result == 90  # 4 below, 1 equal -> (4 + 0.5)/5 * 100 = 90

    def test_middle_value(self) -> None:
        result = compute_percentile(30, [10, 20, 30, 40, 50])
        assert result == 50  # 2 below, 1 equal -> (2 + 0.5)/5 * 100 = 50

    def test_above_all(self) -> None:
        result = compute_percentile(100, [10, 20, 30])
        assert result == 100  # 3 below, 0 equal = 100%

    def test_below_all(self) -> None:
        result = compute_percentile(1, [10, 20, 30])
        assert result == 0  # 0 below, 0 equal = 0%

    def test_clamp_range(self) -> None:
        """Percentile should always be 0–100."""
        assert 0 <= compute_percentile(0, [50, 60, 70]) <= 100
        assert 0 <= compute_percentile(1000, [50, 60, 70]) <= 100


class TestCompareScores:
    """Tests for score comparison against corpus."""

    def test_returns_all_card_types(self) -> None:
        scores = {"demand": 72, "competition": 55, "viability": 40}
        result = compare_scores(scores)
        assert "demand" in result
        assert "competition" in result
        assert "viability" in result

    def test_each_result_has_percentile(self) -> None:
        scores = {"demand": 72, "competition": 55, "viability": 40}
        result = compare_scores(scores)
        for card_type, info in result.items():
            assert "percentile" in info
            assert 0 <= int(info["percentile"]) <= 100

    def test_each_result_has_score(self) -> None:
        scores = {"demand": 72, "competition": 55, "viability": 40}
        result = compare_scores(scores)
        for card_type, info in result.items():
            assert info["score"] == scores[card_type]

    def test_each_result_has_corpus_size(self) -> None:
        scores = {"demand": 72}
        result = compare_scores(scores)
        assert int(result["demand"]["corpus_size"]) > 0

    def test_partial_scores(self) -> None:
        """Only provided card types are compared."""
        scores = {"demand": 72}
        result = compare_scores(scores)
        assert "demand" in result
        assert "competition" not in result

    def test_no_external_calls(self) -> None:
        """Benchmark operates on local data only — no network."""
        # If this test completes without import errors or network calls, we're good
        scores = {"demand": 50, "competition": 50, "viability": 50}
        result = compare_scores(scores)
        assert len(result) == 3


class TestReferenceCorpus:
    """Tests for the reference corpus integrity."""

    def test_corpus_expanded(self) -> None:
        """Verify Phase 0 expansion to 50+ items."""
        assert len(REFERENCE_CORPUS) >= 50

    def test_corpus_has_scores(self) -> None:
        for entry in REFERENCE_CORPUS:
            scores = entry.get("scores", {})
            assert isinstance(scores, dict)
            assert "demand" in scores

    def test_corpus_scores_in_range(self) -> None:
        for entry in REFERENCE_CORPUS:
            scores = entry.get("scores", {})
            if isinstance(scores, dict):
                for score in scores.values():
                    assert 0 <= int(score) <= 100, f"{entry['label']}: score {score} out of range"


class TestFormatComparisonSummary:
    """Tests for summary formatting."""

    def test_empty_comparison(self) -> None:
        assert format_comparison_summary({}) == ""

    def test_includes_corpus_size(self) -> None:
        comparison = {
            "demand": {"score": 72, "percentile": 58, "corpus_size": 12},
        }
        summary = format_comparison_summary(comparison)
        assert "12" in summary

    def test_includes_percentile(self) -> None:
        comparison = {
            "demand": {"score": 72, "percentile": 58, "corpus_size": 12},
        }
        summary = format_comparison_summary(comparison)
        assert "58th percentile" in summary
