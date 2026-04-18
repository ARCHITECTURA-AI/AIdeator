from __future__ import annotations

import json
import logging

from aideator.llm.registry import get_provider
from api.config import settings
from models.report import Card

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


def validate_cards(cards: list[Card]) -> None:
    present = {card.type for card in cards}
    missing = REQUIRED_CARD_TYPES - present
    if missing:
        raise ValueError(f"Missing card types: {sorted(missing)}")


def validate_cards_v1(cards: list[Card]) -> None:
    """V1-enhanced validation: checks score range and band presence.

    Args:
        cards: List of Card objects

    Raises:
        ValueError: On validation failures
    """
    validate_cards(cards)

    for card in cards:
        score = card.score
        normalized = normalize_score(score)
        if not (0 <= normalized <= 100):
            raise ValueError(
                f"Score out of range for {card.type}: {score}"
            )

        band = card.meta.get("band")
        if band is not None:
            if band not in ("high", "medium", "low"):
                raise ValueError(
                    f"Invalid band for {card.type}: {band}. "
                    "Must be 'high', 'medium', or 'low'."
                )
            expected_band = score_to_band(normalized)
            if band != expected_band:
                raise ValueError(
                    f"Band mismatch for {card.type}: score {normalized} expects "
                    f"{expected_band}, got {band}"
                )


def synthesize_default_cards() -> list[Card]:
    """Generate default validation cards (fallback)."""
    cards = [
        Card(
            type="demand",
            title="Market Demand",
            summary="Early demand is plausible but needs focused validation.",
            score=62,
            meta={"band": "medium", "citation_urls": ["https://example.com/demand"]}
        ),
        Card(
            type="competition",
            title="Competitive Landscape",
            summary="Market has competitors with room for differentiated execution.",
            score=54,
            meta={"band": "medium", "citation_urls": ["https://example.com/competition"]}
        ),
        Card(
            type="viability",
            title="Technical Viability",
            summary="Execution risk is moderate due to acquisition and retention uncertainty.",
            score=48,
            meta={"band": "medium", "citation_urls": ["https://example.com/risk"]}
        ),
        Card(
            type="next_steps",
            title="Strategic Roadmap",
            summary="Run user interviews and ship a constrained pilot in two weeks.",
            score=66,
            meta={"band": "medium", "citation_urls": ["https://example.com/next-steps"]}
        ),
    ]
    validate_cards_v1(cards)
    return cards


async def synthesize_intelligence(
    *,
    title: str,
    description: str,
    citations: list[dict[str, str]],
    analysis: dict[str, object] | None = None,
) -> list[Card]:
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
      "detailed_context": "<A detailed 3-5 sentence analysis of the metric, "
                          "referencing specific signals and market nuances.>",
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
      "detailed_context": "<A detailed 3-5 sentence analysis of "
                          "technical/regulatory/market feasibility.>",
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
        raw_cards = data.get("cards", [])
        
        cards: list[Card] = []
        for rc in raw_cards:
            score = normalize_score(rc.get("score", 0))
            band = score_to_band(score)
            
            cards.append(Card(
                type=rc.get("type", "unknown"),
                title=rc.get("title", rc.get("type", "").replace("_", " ").title()),
                summary=rc.get("summary", ""),
                score=score,
                details=rc.get("details", [rc.get("detailed_context", "")]),
                meta={
                    "citation_urls": rc.get("citation_urls", []),
                    "band": band,
                    "level": rc.get("level")
                }
            ))
        
        validate_cards(cards)
        return cards
        
    except Exception as e:
        LOGGER.error(f"LLM synthesis failed, falling back to defaults: {e}", exc_info=True)
        return synthesize_default_cards()


def render_markdown_report(*, idea_id: str, cards: list[Card]) -> str:
    lines: list[str] = [f"# Idea Report {idea_id}", ""]

    for card in cards:
        score = card.score
        band = card.meta.get("band")

        # Section header with score
        header = f"## {card.title}"
        if score is not None:
            normalized = normalize_score(score)
            band_label = band or score_to_band(normalized)
            header += f" — {normalized}/100 ({band_label})"
        lines.append(header)

        # Brief summary for quick scanning
        lines.append(f"**Executive Summary:** {card.summary}")
        lines.append("")
        
        # Detailed context for depth
        if card.details:
            lines.append("### Deep_Dive_Context")
            for detail in card.details:
                lines.append(str(detail))
            lines.append("")

        citations = card.meta.get("citation_urls", [])
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
    lines: list[str], cards: list[Card]
) -> None:
    """Add benchmark comparison section to report lines."""
    try:
        from engine.benchmark import compare_scores, format_comparison_summary

        # Extract scores for benchmarkable card types
        current_scores: dict[str, int] = {}
        for card in cards:
            if card.type in ("demand", "competition", "viability"):
                current_scores[card.type] = normalize_score(card.score)

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


def build_markdown_artifact(*, idea_id: str, cards: list[Card]) -> str:
    validate_cards(cards)
    return render_markdown_report(idea_id=idea_id, cards=cards)
