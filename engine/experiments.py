"""Experiment Engine for generating behavioral validation kits (Smoke Tests)."""

from __future__ import annotations

import json
import logging
from typing import Any

from aideator.llm.registry import get_provider
from engine.retry import resilient_call
from models.report import ExperimentKit

LOGGER = logging.getLogger("engine.experiments")

@resilient_call(retries=3, base_delay=2.0)
async def generate_experiment_kit(
    *,
    title: str,
    description: str,
    analysis_results: dict[str, Any] | None = None,
) -> ExperimentKit:
    """Generate a behavioral experiment blueprint based on the idea and analysis.

    Args:
        title: Idea title.
        description: Idea description.
        analysis_results: Results from Dimensional Analysis for context.

    Returns:
        ExperimentKit object with copy, metrics, and tools.
    """
    from api.config import settings
    provider = get_provider(settings)

    # Context from analysis if available
    if analysis_results and "details" in analysis_results:
        context_text = analysis_results["details"][:200]
    else:
        context_text = "the core problem"

    prompt = f"""You are an Expert Growth Marketer and Experiment Designer.
Your task is to design a "Smoke Test" experiment for a new business idea.

IDEA:
Title: {title}
Description: {description}
Context: {context_text}

The experiment should be designed to move from "intent" (interviews) 
to "commitment" (behavioral data).

GENERATION RULES:
1. HYPOTHESIS: State it as "If I [action], then [number/percent] of 
   [audience] will [commitment action]."
2. LANDING PAGE COPY: Use the PAS (Problem, Agitation, Solution) framework.
   - Headline: Attention-grabbing benefit.
   - Hero Subheadline: Clear value prop.
   - Pain Points: 3 bullet points that hurt.
   - Solution: How we fix it.
   - CTA: Strong action (e.g., "Join the Early Access", "Pre-order Now").
3. SUCCESS METRIC: Define a "Fail-Fast" threshold for a 48-hour or 1-week test.
4. TOOL STACK: Recommend 2-3 specific no-code tools (e.g., Carrd, Framer, Tally, Loops, Stripe).

Return a JSON object with:
{{
  "hypothesis": "...",
  "method": "Smoke Test / Landing Page",
  "landing_page_copy": {{
    "headline": "...",
    "subheadline": "...",
    "pain_points": ["...", "...", "..."],
    "solution": "...",
    "cta": "..."
  }},
  "success_metric": "...",
  "tool_stack": ["...", "..."]
}}
"""
    messages = [{"role": "user", "content": prompt}]
    response = await provider.generate(messages, temperature=0.3)
    
    content = response.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    data = json.loads(content)
    
    # Ensure landing_page_copy is flattened correctly if needed, 
    # but our model expects a dict[str, str]. 
    # Let's adjust the data to match dict[str, str] by joining pain points.
    copy = data.get("landing_page_copy", {})
    if isinstance(copy.get("pain_points"), list):
        copy["pain_points"] = "\n".join(copy["pain_points"])
        
    return ExperimentKit(
        hypothesis=data.get("hypothesis", "If I launch a landing page, people will sign up."),
        method=data.get("method", "Smoke Test"),
        landing_page_copy=copy,
        success_metric=data.get("success_metric", "5% conversion rate"),
        tool_stack=data.get("tool_stack", ["Carrd", "Tally"])
    )
