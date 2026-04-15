from __future__ import annotations

import json
import logging
from aideator.llm.registry import get_provider
from api.config import settings

LOGGER = logging.getLogger("engine.synthesizer")

REQUIRED_CARD_TYPES = {"demand", "competition", "viability", "next_steps"}
REQUIRES_CITATIONS = {"demand", "competition", "viability"}

# Band thresholds for 0–100 scoring (V1)
BAND_HIGH_THRESHOLD = 70
BAND_LOW_THRESHOLD = 40


def score_to_band(score: int | float) -> str:
    """Convert a numeric score to a band label.

    Args:
        score: Numeric score (0–100)

    Returns:
        Band label: 'high', 'medium', or 'low'
    """
    if score >= BAND_HIGH_THRESHOLD:
        return "high"
    if score >= BAND_LOW_THRESHOLD:
        return "medium"
    return "low"


def normalize_score(score: int | float) -> int:
    """Normalize a score to 0–100 integer range.

    Handles both legacy 0.0–1.0 floats and new 0–100 integers.

    Args:
        score: Raw score value

    Returns:
        Integer score in [0, 100]
    """
    if isinstance(score, float) and 0.0 <= score <= 1.0:
        # Legacy format: convert 0.0–1.0 to 0–100
        return round(score * 100)
    return max(0, min(100, int(score)))


def validate_cards(cards: list[dict[str, object]]) -> None:
    present = {str(card.get("type")) for card in cards}
    missing = REQUIRED_CARD_TYPES - present
    if missing:
        raise ValueError(f"Missing card types: {sorted(missing)}")

    for card in cards:
        card_type = str(card.get("type"))
        citations = card.get("citation_urls", [])
        if card_type in REQUIRES_CITATIONS and (
            not isinstance(citations, list) or len(citations) == 0
        ):
            raise ValueError(f"Missing citations for card type: {card_type}")


def validate_cards_v1(cards: list[dict[str, object]]) -> None:
    """V1-enhanced validation: checks score range and band presence.

    Args:
        cards: List of card dicts

    Raises:
        ValueError: On validation failures
    """
    validate_cards(cards)

    for card in cards:
        score = card.get("score")
        if score is not None:
            normalized = normalize_score(score)
            if not (0 <= normalized <= 100):
                raise ValueError(
                    f"Score out of range for {card.get('type')}: {score}"
                )

        band = card.get("band")
        if band is not None and band not in ("high", "medium", "low"):
            raise ValueError(
                f"Invalid band for {card.get('type')}: {band}. "
                "Must be 'high', 'medium', or 'low'."
            )

        # If score present but band missing, that's OK — we auto-compute
        # But if band is present, it must match the score
        if score is not None and band is not None:
            expected_band = score_to_band(normalize_score(score))
            if band != expected_band:
                raise ValueError(
                    f"Band mismatch for {card.get('type')}: "
                    f"score {score} should be '{expected_band}', got '{band}'"
                )


def synthesize_default_cards() -> list[dict[str, object]]:
    """Generate default validation cards (fallback)."""
    cards: list[dict[str, object]] = [
        {
            "type": "demand",
            "score": 62,
            "band": "medium",
            "summary": "Early demand is plausible but needs focused validation.",
            "citation_urls": ["https://example.com/demand"],
        },
        {
            "type": "competition",
            "score": 54,
            "level": "Moderate",
            "band": "medium",
            "summary": "Market has competitors with room for differentiated execution.",
            "citation_urls": ["https://example.com/competition"],
        },
        {
            "type": "viability",
            "score": 48,
            "band": "medium",
            "summary": "Execution risk is moderate due to acquisition and retention uncertainty.",
            "citation_urls": ["https://example.com/risk"],
        },
        {
            "type": "next_steps",
            "score": 66,
            "band": "medium",
            "summary": "Run user interviews and ship a constrained pilot in two weeks.",
            "citation_urls": ["https://example.com/next-steps"],
        },
    ]
    validate_cards_v1(cards)
    return cards


async def synthesize_intelligence(
    *,
    title: str,
    description: str,
    citations: list[dict[str, str]],
    analysis: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    """Synthesize intelligence cards using LLM.

    This is 'Node 3' of the research graph. It takes the structured analysis
    from Node 2 and synthesizes it into the final public-facing cards.

    Args:
        title: Idea title
        description: Idea description
        citations: Collected signal snippets
        analysis: Dimensional analysis results from Node 2

    Returns:
        List of card dictionaries
    """
    try:
        provider = get_provider(settings)
        
        signals_text = "\n".join(
            [f"- [{c['source_id']}] {c['content']} (URL: {c['url']})" for c in citations]
        )
        
        analysis_json = json.dumps(analysis, indent=2) if analysis else "{}"
        
        prompt = f"""You are a Lead Business Intelligence Architect. 
Your goal is to synthesize the final validation report for the idea: "{title}".

DESCRIPTION:
{description}

SIGNALS:
{signals_text}

DIMENSIONAL ANALYSIS (Context from the Analyst Node):
{analysis_json}

Using the Analyst's findings and the raw signals, produce the final 4-card synthesis.
Each card must balance quantitative scoring with deep qualitative context.

Return ONLY a JSON object with this exact structure:
{{
  "cards": [
    {{
      "type": "demand",
      "score": <int 0-100>,
      "summary": "<1-2 sentence executive summary>",
      "detailed_context": "<A detailed 3-5 sentence analysis of the metric, referencing specific signals and market nuances.>",
      "citation_urls": [<list of URLs actually referenced>]
    }},
    {{
      "type": "competition",
      "score": <int 0-100>,
      "level": "Low/Moderate/High/Critical",
      "summary": "<1-2 sentence executive summary>",
      "detailed_context": "<A detailed 3-5 sentence analysis of the competitive landscape.>",
      "citation_urls": [<list of URLs actually referenced>]
    }},
    {{
      "type": "viability",
      "score": <int 0-100>,
      "summary": "<1-2 sentence executive summary>",
      "detailed_context": "<A detailed 3-5 sentence analysis of technical/regulatory/market feasibility.>",
      "citation_urls": [<list of URLs actually referenced>]
    }},
    {{
      "type": "next_steps",
      "score": <int 0-100>,
      "summary": "<1-2 sentence executive summary>",
      "detailed_context": "<A detailed 3-5 sentence actionable roadmap.>",
      "citation_urls": [<list of URLs actually referenced>]
    }}
  ]
}}
"""
        messages = [{"role": "user", "content": prompt}]
        response = await provider.generate(messages, temperature=0.7)
        
        # Extract JSON from response
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
             content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        cards = data.get("cards", [])
        
        # Post-process: Add bands if missing
        for card in cards:
            if "score" in card and "band" not in card:
                card["band"] = score_to_band(normalize_score(card["score"]))
        
        validate_cards_v1(cards)
        return cards
        
    except Exception as e:
        LOGGER.error(f"LLM synthesis failed, falling back to defaults: {e}", exc_info=True)
        return synthesize_default_cards()


def render_markdown_report(*, idea_id: str, cards: list[dict[str, object]]) -> str:
    lines: list[str] = [f"# Idea Report {idea_id}", ""]

    for card in cards:
        card_type = str(card.get("type", "unknown"))
        score = card.get("score")
        band = card.get("band")

        # Section header with score
        header = f"## {card_type.replace('_', ' ').title()}"
        if score is not None:
            normalized = normalize_score(score)
            band_label = band or score_to_band(normalized)
            header += f" — {normalized}/100 ({band_label})"
        lines.append(header)

        # Brief summary for quick scanning
        lines.append(f"**Executive Summary:** {card.get('summary', '')}")
        lines.append("")
        
        # Detailed context for depth
        detailed = card.get("detailed_context")
        if detailed:
            lines.append("### Deep_Dive_Context")
            lines.append(str(detailed))
            lines.append("")

        citations = card.get("citation_urls", [])
        if isinstance(citations, list) and citations:
            lines.append("")
            lines.append("Citations:")
            for url in citations:
                lines.append(f"- {url}")
        lines.append("")

    # Benchmark comparison section
    _append_benchmark_section(lines, cards)

    lines.append("## Cursor/Claude Code Usage Notes")
    lines.append("Artifact rendered from validated cards.")
    lines.append("")
    return "\n".join(lines)


def _append_benchmark_section(
    lines: list[str], cards: list[dict[str, object]]
) -> None:
    """Add benchmark comparison section to report lines."""
    try:
        from engine.benchmark import compare_scores, format_comparison_summary

        # Extract scores for benchmarkable card types
        current_scores: dict[str, int] = {}
        for card in cards:
            card_type = str(card.get("type", ""))
            score = card.get("score")
            if card_type in ("demand", "competition", "viability") and score is not None:
                current_scores[card_type] = normalize_score(score)

        if current_scores:
            comparison = compare_scores(current_scores)
            summary = format_comparison_summary(comparison)
            if summary:
                lines.append("## Benchmark Comparison")
                lines.append(summary)
                lines.append("")
    except ImportError:
        # Benchmark module not available — skip silently
        pass


def build_markdown_artifact(*, idea_id: str, cards: list[dict[str, object]]) -> str:
    validate_cards(cards)
    return render_markdown_report(idea_id=idea_id, cards=cards)
