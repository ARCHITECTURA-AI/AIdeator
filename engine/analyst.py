from __future__ import annotations

import json
import logging
from typing import Any

from aideator.llm.registry import get_provider
from api.config import settings

LOGGER = logging.getLogger("engine.analyst")


async def analyze_dimensions(
    *,
    title: str,
    description: str,
    citations: list[dict[str, Any]],
) -> dict[str, object]:
    """Analyze collected signals across dimensions.

    This is 'Node 2' of the research graph. It sifts through raw citations
    and organizes them into dimensional insights (Demand, Competition, Viability).

    Args:
        title: Idea title
        description: Idea description
        citations: Collected signal snippets

    Returns:
        Dictionary containing dimensional analysis
    """
    try:
        provider = get_provider(settings)

        signals_text = "\n".join(
            [
                f"- [{c['source_id']}] "
                f"[Type: {c.get('type', 'unknown')}, "
                f"Confidence: {c.get('confidence', 0.5)}] "
                f"{c['content']} (URL: {c['url']})"
                for c in citations
            ]
        )

        prompt = f"""You are a High-Precision Market Analyst. 
Analyze the provided signals for the business idea: "{title}".

DESCRIPTION:
{description}

SIGNALS:
{signals_text}

Your task is to organize these signals into three structured dimensional analyses:
1. DEMAND: Is there evidence of a problem, pain point, or desire?
2. COMPETITION: Who else is solving this? What is the intensity?
3. VIABILITY: Are there clear technical, regulatory, or economic hurdles?
4. MARKET_SIZING: Based on signals, estimate the TAM (Total Addressable Market),
   SAM (Serviceable Addressable Market), and SOM (Serviceable Obtainable Market) in USD.

WEIGHTING RULES:
- PRIORITIZE signals with type 'pain_complaint', 'feature_request', or 'competitor_weakness'.
  These are high-intent signals.
- TREAT signals with type 'seo_filler' or low confidence (< 0.4) as noise.
  Do not let them drive major score changes.
- HIGH CONFIDENCE 'pain_complaint' is your strongest evidence for Demand.

For each of the first three dimensions, provide:
- "strengths": Signals clearly supporting the case.
- "weaknesses": Signals suggesting risks or lack of market fit.
- "synthesis_preamble": A short summary of the evidence found for this specific dimension.

For MARKET_SIZING, provide:
- "tam": A string with the estimated value and brief logic.
- "sam": A string with the estimated value and brief logic.
- "som": A string with the estimated value and brief logic.

Return ONLY a JSON object with this structure:
{{
  "demand": {{ "strengths": [], "weaknesses": [], "synthesis_preamble": "" }},
  "competition": {{ "strengths": [], "weaknesses": [], "synthesis_preamble": "" }},
  "viability": {{ "strengths": [], "weaknesses": [], "synthesis_preamble": "" }},
  "market_sizing": {{ "tam": "", "sam": "", "som": "" }}
}}
"""
        messages = [{"role": "user", "content": prompt}]
        response = await provider.generate(messages, temperature=0.3)

        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return json.loads(content)

    except Exception as e:
        LOGGER.error(f"Dimensional analysis failed: {e}", exc_info=True)
        # Fallback to empty structure
        return {
            "demand": {
                "strengths": [],
                "weaknesses": [],
                "synthesis_preamble": "Analysis failed, defaulting to synthetic synthesis.",
            },
            "competition": {
                "strengths": [],
                "weaknesses": [],
                "synthesis_preamble": "Analysis failed.",
            },
            "viability": {
                "strengths": [],
                "weaknesses": [],
                "synthesis_preamble": "Analysis failed.",
            },
            "market_sizing": {"tam": "N/A", "sam": "N/A", "som": "N/A"},
        }
