from __future__ import annotations

import json
import logging

from aideator.llm.registry import get_provider
from api.config import settings

LOGGER = logging.getLogger("engine.analyst")

async def analyze_dimensions(
    *,
    title: str,
    description: str,
    citations: list[dict[str, str]],
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
            [f"- [{c['source_id']}] {c['content']} (URL: {c['url']})" for c in citations]
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

For each dimension, provide:
- "strengths": Signals clearly supporting the case.
- "weaknesses": Signals suggesting risks or lack of market fit.
- "synthesis_preamble": A short summary of the evidence found for this specific dimension.

Return ONLY a JSON object with this structure:
{{
  "demand": {{ "strengths": [], "weaknesses": [], "synthesis_preamble": "" }},
  "competition": {{ "strengths": [], "weaknesses": [], "synthesis_preamble": "" }},
  "viability": {{ "strengths": [], "weaknesses": [], "synthesis_preamble": "" }}
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
                "synthesis_preamble": "Analysis failed, defaulting to synthetic synthesis."
            },
            "competition": {
                "strengths": [], 
                "weaknesses": [], 
                "synthesis_preamble": "Analysis failed."
            },
            "viability": {
                "strengths": [], 
                "weaknesses": [], 
                "synthesis_preamble": "Analysis failed."
            }
        }
