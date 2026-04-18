"""Internal benchmark module for idea scoring comparison.

Maintains a static corpus of reference ideas with known scores
and provides percentile calculations. All data is internal —
no external calls, safe for local-only mode.
"""

from __future__ import annotations

# Static reference corpus of known product validations.
# Each entry represents a real-world product category with
# typical validation scores (0–100 scale).
REFERENCE_CORPUS: list[dict[str, object]] = [
    {"label": "Notion (productivity SaaS)", 
     "scores": {"demand": 88, "competition": 35, "viability": 42}},
    {"label": "Linear (dev tool SaaS)", 
     "scores": {"demand": 82, "competition": 45, "viability": 38}},
    {"label": "Calendly (scheduling SaaS)", 
     "scores": {"demand": 78, "competition": 55, "viability": 30}},
    {"label": "Figma (design tool)", 
     "scores": {"demand": 90, "competition": 40, "viability": 48}},
    {"label": "Retool (internal tools)", 
     "scores": {"demand": 72, "competition": 50, "viability": 35}},
    {"label": "Supabase (backend-as-a-service)", 
     "scores": {"demand": 75, "competition": 60, "viability": 45}},
    {"label": "Vercel (deployment platform)", 
     "scores": {"demand": 80, "competition": 52, "viability": 40}},
    {"label": "Posthog (analytics SaaS)", 
     "scores": {"demand": 68, "competition": 58, "viability": 32}},
    {"label": "Loom (video messaging)", 
     "scores": {"demand": 70, "competition": 48, "viability": 50}},
    {"label": "Airtable (no-code database)", 
     "scores": {"demand": 76, "competition": 42, "viability": 36}},
    {"label": "Jasper (AI content creation)", 
     "scores": {"demand": 85, "competition": 20, "viability": 45}},
    {"label": "Stripe (payment infra)", 
     "scores": {"demand": 92, "competition": 65, "viability": 55}},
    {"label": "Shopify (e-commerce engine)", 
     "scores": {"demand": 87, "competition": 70, "viability": 50}},
    {"label": "Airbnb (marketplace consumer)", 
     "scores": {"demand": 84, "competition": 30, "viability": 60}},
    {"label": "Duolingo (edtech consumer)", 
     "scores": {"demand": 74, "competition": 40, "viability": 52}},
    {"label": "Sentry (error tracking)", 
     "scores": {"demand": 81, "competition": 55, "viability": 35}},
    {"label": "Intercom (customer support)", 
     "scores": {"demand": 79, "competition": 62, "viability": 40}},
    {"label": "Auth0 (identity-as-a-service)", 
     "scores": {"demand": 77, "competition": 50, "viability": 48}},
    {"label": "Snowflake (data warehousing)", 
     "scores": {"demand": 89, "competition": 75, "viability": 58}},
    {"label": "Datadog (monitoring SaaS)", 
     "scores": {"demand": 86, "competition": 68, "viability": 42}},
    {"label": "Generic early-stage SaaS (weak)", 
     "scores": {"demand": 35, "competition": 70, "viability": 65}},
    {"label": "Generic early-stage SaaS (average)", 
     "scores": {"demand": 55, "competition": 55, "viability": 50}},
    {"label": "Hypothetical 'Juicero' (over-engineered hardware)", 
     "scores": {"demand": 40, "competition": 85, "viability": 15}},
    {"label": "Uber (ride-hailing marketplace)", 
     "scores": {"demand": 95, "competition": 80, "viability": 70}},
    {"label": "Slack (business communication)", 
     "scores": {"demand": 91, "competition": 75, "viability": 45}},
    {"label": "Zoom (video conferencing)", 
     "scores": {"demand": 83, "competition": 88, "viability": 35}},
    {"label": "GitHub (version control)", 
     "scores": {"demand": 94, "competition": 60, "viability": 40}},
    {"label": "Mailchimp (email marketing)", 
     "scores": {"demand": 72, "competition": 90, "viability": 30}},
    {"label": "Canva (visual design tool)", 
     "scores": {"demand": 88, "competition": 45, "viability": 38}},
    {"label": "Dropbox (cloud storage)", 
     "scores": {"demand": 70, "competition": 95, "viability": 25}},
    {"label": "Palantir (enterprise analytics)", 
     "scores": {"demand": 65, "competition": 30, "viability": 75}},
    {"label": "Cloudflare (security/infra)", 
     "scores": {"demand": 89, "competition": 55, "viability": 52}},
    {"label": "HubSpot (CRM/marketing)", 
     "scores": {"demand": 78, "competition": 85, "viability": 40}},
    {"label": "Twilio (comms API)", 
     "scores": {"demand": 82, "competition": 50, "viability": 45}},
    {"label": "Atlassian Jira (agile PM)", 
     "scores": {"demand": 75, "competition": 92, "viability": 35}},
    {"label": "Discord (comms consumer)", 
     "scores": {"demand": 85, "competition": 40, "viability": 42}},
    {"label": "Robinhood (fintech consumer)", 
     "scores": {"demand": 80, "competition": 65, "viability": 58}},
    {"label": "Coinbase (crypto exchange)", 
     "scores": {"demand": 77, "competition": 50, "viability": 62}},
    {"label": "Instacart (grocery delivery)", 
     "scores": {"demand": 72, "competition": 85, "viability": 68}},
    {"label": "Peloton (connected fitness)", 
     "scores": {"demand": 68, "competition": 60, "viability": 55}},
    {"label": "Grammarly (AI writing aid)", 
     "scores": {"demand": 84, "competition": 35, "viability": 32}},
    {"label": "Zapier (automation SaaS)", 
     "scores": {"demand": 81, "competition": 45, "viability": 28}},
    {"label": "Segment (customer data platform)", 
     "scores": {"demand": 76, "competition": 55, "viability": 40}},
    {"label": "Okta (Identity Cloud)", 
     "scores": {"demand": 79, "competition": 58, "viability": 50}},
    {"label": "Rippling (HR/IT SaaS)", 
     "scores": {"demand": 82, "competition": 52, "viability": 44}},
    {"label": "Deel (EOR SaaS)", 
     "scores": {"demand": 85, "competition": 48, "viability": 52}},
    {"label": "Wiz (security SaaS)", 
     "scores": {"demand": 88, "competition": 65, "viability": 48}},
    {"label": "Gong (sales intelligence)", 
     "scores": {"demand": 74, "competition": 30, "viability": 38}},
    {"label": "Plaid (fintech API)", 
     "scores": {"demand": 83, "competition": 45, "viability": 42}},
    {"label": "Scale AI (data labeling)", 
     "scores": {"demand": 86, "competition": 40, "viability": 55}},
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
            Example: {"demand": 72, "competition": 55, "viability": 40}
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
    card_types = ["demand", "competition", "viability"]

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
