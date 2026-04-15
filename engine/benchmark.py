"""Internal benchmark module for idea scoring comparison.

Maintains a static corpus of reference ideas with known scores
and provides percentile calculations. All data is internal —
no external calls, safe for local-only mode.
"""

from __future__ import annotations

from dataclasses import dataclass

# Static reference corpus of known product validations.
# Each entry represents a real-world product category with
# typical validation scores (0–100 scale).
REFERENCE_CORPUS: list[dict[str, object]] = [
    {
        "label": "Notion (productivity SaaS)",
        "scores": {"demand": 88, "competition": 35, "risk": 42},
    },
    {
        "label": "Linear (dev tool SaaS)",
        "scores": {"demand": 82, "competition": 45, "risk": 38},
    },
    {
        "label": "Calendly (scheduling SaaS)",
        "scores": {"demand": 78, "competition": 55, "risk": 30},
    },
    {
        "label": "Figma (design tool)",
        "scores": {"demand": 90, "competition": 40, "risk": 48},
    },
    {
        "label": "Retool (internal tools)",
        "scores": {"demand": 72, "competition": 50, "risk": 35},
    },
    {
        "label": "Supabase (backend-as-a-service)",
        "scores": {"demand": 75, "competition": 60, "risk": 45},
    },
    {
        "label": "Vercel (deployment platform)",
        "scores": {"demand": 80, "competition": 52, "risk": 40},
    },
    {
        "label": "Posthog (analytics SaaS)",
        "scores": {"demand": 68, "competition": 58, "risk": 32},
    },
    {
        "label": "Loom (video messaging)",
        "scores": {"demand": 70, "competition": 48, "risk": 50},
    },
    {
        "label": "Airtable (no-code database)",
        "scores": {"demand": 76, "competition": 42, "risk": 36},
    },
    {
        "label": "Generic early-stage SaaS (weak)",
        "scores": {"demand": 35, "competition": 70, "risk": 65},
    },
    {
        "label": "Generic early-stage SaaS (average)",
        "scores": {"demand": 55, "competition": 55, "risk": 50},
    },
]


def _get_corpus_scores(card_type: str) -> list[int]:
    """Extract all scores for a given card type from the corpus."""
    scores: list[int] = []
    for entry in REFERENCE_CORPUS:
        entry_scores = entry.get("scores", {})
        if isinstance(entry_scores, dict) and card_type in entry_scores:
            scores.append(int(entry_scores[card_type]))
    return sorted(scores)


def compute_percentile(value: int, sorted_values: list[int]) -> int:
    """Compute the percentile of a value within a sorted list.

    Uses the 'percentage of values below' method.

    Args:
        value: The score to evaluate
        sorted_values: Sorted list of reference scores

    Returns:
        Percentile (0–100)
    """
    if not sorted_values:
        return 50  # No data → median assumption

    count_below = sum(1 for v in sorted_values if v < value)
    count_equal = sum(1 for v in sorted_values if v == value)

    # Interpolated percentile
    percentile = ((count_below + 0.5 * count_equal) / len(sorted_values)) * 100
    return max(0, min(100, round(percentile)))


def compare_scores(
    current_scores: dict[str, int],
    corpus: list[dict[str, object]] | None = None,
) -> dict[str, dict[str, int | str]]:
    """Compare current idea scores against the reference corpus.

    Args:
        current_scores: Dict mapping card type to score (0–100).
            Example: {"demand": 72, "competition": 55, "risk": 40}
        corpus: Optional custom corpus. Defaults to REFERENCE_CORPUS.

    Returns:
        Dict mapping card type to percentile info.
        Example: {
            "demand": {"score": 72, "percentile": 58, "corpus_size": 12},
            "competition": {"score": 55, "percentile": 65, "corpus_size": 12},
        }
    """
    if corpus is None:
        corpus = REFERENCE_CORPUS

    result: dict[str, dict[str, int | str]] = {}
    card_types = ["demand", "competition", "risk"]

    for card_type in card_types:
        if card_type not in current_scores:
            continue

        score = current_scores[card_type]
        corpus_scores = _get_corpus_scores(card_type)
        percentile = compute_percentile(score, corpus_scores)

        result[card_type] = {
            "score": score,
            "percentile": percentile,
            "corpus_size": len(corpus_scores),
        }

    return result


def format_comparison_summary(
    comparison: dict[str, dict[str, int | str]],
) -> str:
    """Format comparison results as a human-readable summary.

    Args:
        comparison: Output from compare_scores()

    Returns:
        Formatted text string for report inclusion
    """
    if not comparison:
        return ""

    corpus_size = 0
    lines: list[str] = []

    for card_type, info in comparison.items():
        percentile = info["percentile"]
        corpus_size = int(info.get("corpus_size", 0))
        label = card_type.replace("_", " ").title()
        lines.append(f"- **{label}**: {percentile}th percentile")

    header = f"Compared to {corpus_size} similar ideas:"
    return header + "\n" + "\n".join(lines)
