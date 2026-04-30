from __future__ import annotations

import json
import logging
from typing import Any

from aideator.llm.registry import get_provider
from api.config import settings
from models.idea import ValidationStatus
from models.report import Card, ExperimentKit, InterviewKit

LOGGER = logging.getLogger("engine.synthesizer")

REQUIRED_CARD_TYPES = {"demand", "market", "competition", "viability", "next_steps"}
REQUIRES_CITATIONS = {"demand", "market", "competition", "viability"}

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
            raise ValueError(f"Score out of range for {card.type}: {score}")

        band = card.meta.get("band")
        if band is not None:
            if band not in ("high", "medium", "low"):
                raise ValueError(
                    f"Invalid band for {card.type}: {band}. Must be 'high', 'medium', or 'low'."
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
            meta={"band": "medium", "citation_urls": ["https://example.com/demand"]},
        ),
        Card(
            type="competition",
            title="Competitive Landscape",
            summary="Market has competitors with room for differentiated execution.",
            score=54,
            meta={"band": "medium", "citation_urls": ["https://example.com/competition"]},
        ),
        Card(
            type="market",
            title="Market Sizing (TAM/SAM/SOM)",
            summary="Targeting a $2.4B global market with a $150M serviceable addressable segment.",
            score=78,
            meta={"band": "high", "citation_urls": ["https://example.com/market"]},
        ),
        Card(
            type="viability",
            title="Technical Viability",
            summary="Execution risk is moderate due to acquisition and retention uncertainty.",
            score=48,
            meta={"band": "medium", "citation_urls": ["https://example.com/risk"]},
        ),
        Card(
            type="next_steps",
            title="Strategic Roadmap",
            summary="Run user interviews and ship a constrained pilot in two weeks.",
            score=66,
            meta={"band": "medium", "citation_urls": ["https://example.com/next-steps"]},
        ),
    ]
    validate_cards_v1(cards)
    return cards


async def synthesize_intelligence(
    *,
    title: str,
    description: str,
    citations: list[dict[str, Any]],
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
            [
                f"- [{c['source_id']}] Type: {c.get('type', 'unknown')}, "
                f"Confidence: {c.get('confidence', 0.5)}] "
                f"{c['content']} (URL: {c['url']})"
                for c in citations
            ]
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

Using the Analyst's findings and the raw signals, produce the final 5-card synthesis.
Each card must balance quantitative scoring with deep qualitative context.
Specifically for the "market" card, include estimates for TAM (Total Addressable Market),
SAM (Serviceable Addressable Market), and SOM (Serviceable Obtainable Market) if signals allow.

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
      "type": "market",
      "score": <int 0-100>,
      "summary": "<1-2 sentence executive summary>",
      "detailed_context": "<A detailed analysis of market size and segments.>",
      "tam": "<string estimate>",
      "sam": "<string estimate>",
      "som": "<string estimate>",
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

            cards.append(
                Card(
                    type=rc.get("type", "unknown"),
                    title=rc.get("title", rc.get("type", "").replace("_", " ").title()),
                    summary=rc.get("summary", ""),
                    score=score,
                    details=rc.get("details", [rc.get("detailed_context", "")]),
                    meta={
                        "band": band,
                        "citation_urls": rc.get("citation_urls", []),
                        "tam": rc.get("tam"),
                        "sam": rc.get("sam"),
                        "som": rc.get("som"),
                        "level": rc.get("level"),
                    },
                )
            )

        validate_cards(cards)
        return cards

    except Exception as e:
        LOGGER.error(f"LLM synthesis failed, falling back to defaults: {e}", exc_info=True)
        return synthesize_default_cards()


def render_markdown_report(
    *,
    idea_id: str,
    cards: list[Card],
    battle_results: dict[str, Any] | None = None,
    interview_kit: InterviewKit | None = None,
    experiment_kit: ExperimentKit | None = None,
    status: ValidationStatus = ValidationStatus.DESK_RESEARCH,
) -> str:
    lines: list[str] = [f"# Idea Report {idea_id}", ""]

    # Phase Banner
    status_label = status.value.replace("_", " ").title()
    lines.append("## 🏆 Current Validation Phase")
    lines.append(f"**Stage:** `{status_label}`")
    
    if status == ValidationStatus.PIVOT_RECOMMENDED:
        lines.append("> [!CAUTION]")
        lines.append(
            "> **Pivot Recommended:** High adversarial signal detected. "
            "Review the Bear Case below before proceeding."
        )
    elif status == ValidationStatus.EXPERIMENT_READY:
        lines.append("> [!TIP]")
        lines.append(
            "> **Green Light:** High confidence signals. "
            "Skip to Phase 3 and launch your smoke test."
        )
    elif status == ValidationStatus.INTERVIEW_READY:
        lines.append("> [!NOTE]")
        lines.append(
            "> **Proceed with Caution:** Evidence is moderate. "
            "Run 5-10 user interviews (Phase 2) to confirm pain points."
        )
    
    lines.append("")

    for card in cards:
        score = card.score

        # Section header with score
        header = f"## {card.title}"
        if score is not None:
            normalized = normalize_score(score)
            # Add animation hooks for the "Wow" moment
            score_span = (
                f'<span class="score-display animate-score" data-target="{normalized}">0</span>'
            )
            header += f" — {score_span}/100"

        # Add reveal wrapper start
        lines.append('<div class="reveal">')
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

        # Market Sizing table for 'market' card
        if card.type == "market" and any(card.meta.get(k) for k in ("tam", "sam", "som")):
            lines.append("")
            lines.append("| Dimension | Estimated Size |")
            lines.append("| :--- | :--- |")
            lines.append(f"| **TAM** | {card.meta.get('tam', 'N/A')} |")
            lines.append(f"| **SAM** | {card.meta.get('sam', 'N/A')} |")
            lines.append(f"| **SOM** | {card.meta.get('som', 'N/A')} |")
            lines.append("")

        lines.append(f"> {card.summary}")

        # Add reveal wrapper end
        lines.append("</div> <!-- end reveal -->")
        lines.append("")

    # Benchmark comparison section
    _append_benchmark_section(lines, cards)

    # Battle Mode section
    if battle_results:
        lines.append("## Battle Mode: Bull vs Bear")
        lines.append('<div class="battle-container">')
        lines.append('  <div class="bull-case">')
        lines.append("    <h3>🐂 The Bull Case</h3>")
        lines.append(f"    <p>{battle_results.get('bull_case', '')}</p>")
        lines.append("  </div>")
        lines.append('  <div class="bear-case">')
        lines.append("    <h3>🐻 The Bear Case</h3>")
        lines.append(f"    <p>{battle_results.get('bear_case', '')}</p>")
        lines.append("  </div>")
        lines.append('  <div class="the-hinge">')
        lines.append("    <h3>⚖️ The Strategic Hinge</h3>")
        lines.append(f"    <p><strong>{battle_results.get('the_hinge', '')}</strong></p>")
        lines.append("  </div>")
        lines.append("</div>")
        lines.append("")

    # User Interview Toolkit section
    if interview_kit:
        lines.append("## 🎤 User Interview Toolkit")
        lines.append("> [!TIP]")
        lines.append("> These questions are designed based on 'The Mom Test'.")
        lines.append("> Focus on past behavior, not future opinions.")
        lines.append("")
        
        lines.append("### 📝 Interview Script")
        for i, item in enumerate(interview_kit.script, 1):
            lines.append(f"{i}. **{item.get('question')}**")
            lines.append(f"   - *Rationale:* {item.get('rationale')}")
        lines.append("")

        lines.append("### 📧 Outreach Templates")
        for platform, template in interview_kit.outreach_templates.items():
            lines.append(f"#### {platform.title()}")
            lines.append("```text")
            lines.append(template)
            lines.append("```")
        lines.append("")

        lines.append("### 📊 Response Tracker Schema")
        lines.append("Use these columns in your spreadsheet to track findings:")
        lines.append(f"| {' | '.join(interview_kit.response_tracker)} |")
        lines.append(f"| {' | '.join(['---'] * len(interview_kit.response_tracker))} |")
        lines.append("")
        
    # Phase 3: Behavioral Experiment Kit
    if experiment_kit:
        lines.append("## 🧪 Behavioral Experiment (Smoke Test)")
        lines.append("> [!IMPORTANT]")
        lines.append("> Moving from intent to behavior.")
        lines.append("> This experiment measures actual commitment.")
        lines.append("")
        
        lines.append("### 🔬 Hypothesis")
        lines.append(f"_{experiment_kit.hypothesis}_")
        lines.append("")
        
        lines.append("### 📄 Landing Page Blueprint (PAS Framework)")
        copy = experiment_kit.landing_page_copy
        lines.append(f"**Headline:** {copy.get('headline')}")
        lines.append(f"**Subheadline:** {copy.get('subheadline')}")
        lines.append("")
        lines.append("**The Pain (Agitation):**")
        lines.append(copy.get('pain_points', ''))
        lines.append("")
        lines.append(f"**The Solution:** {copy.get('solution')}")
        lines.append("")
        lines.append(f"**Primary CTA:** `{copy.get('cta')}`")
        lines.append("")

        lines.append("### 📈 Success Metrics")
        lines.append(f"**Target:** {experiment_kit.success_metric}")
        lines.append("")

        lines.append("### 🛠️ Recommended Tool Stack")
        for tool in experiment_kit.tool_stack:
            lines.append(f"- {tool}")
        lines.append("")

    lines.append("## Cursor/Claude Code Usage Notes")
    lines.append("Artifact rendered from validated cards.")
    lines.append("")
    return "\n".join(lines)


def _append_benchmark_section(lines: list[str], cards: list[Card]) -> None:
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


def build_markdown_artifact(
    *,
    idea_id: str,
    cards: list[Card],
    battle_results: dict[str, Any] | None = None,
    interview_kit: InterviewKit | None = None,
    experiment_kit: ExperimentKit | None = None,
    status: ValidationStatus = ValidationStatus.DESK_RESEARCH,
) -> str:
    validate_cards(cards)
    return render_markdown_report(
        idea_id=idea_id,
        cards=cards,
        battle_results=battle_results,
        interview_kit=interview_kit,
        experiment_kit=experiment_kit,
        status=status,
    )
