"""Engine for generating actionable user interview toolkits."""

from __future__ import annotations

import json
import logging
from typing import Any

from aideator.llm.registry import get_provider
from api.config import settings
from engine.retry import resilient_call
from models.report import InterviewKit

LOGGER = logging.getLogger("engine.interviewer")

@resilient_call(retries=3, base_delay=2.0)
async def generate_interview_kit(
    *,
    title: str,
    description: str,
    analysis: dict[str, Any],
    signals: list[dict[str, Any]]
) -> InterviewKit:
    """Generate a customized interview kit based on validation results.
    
    Args:
        title: Idea title
        description: Idea description
        analysis: Dimensional analysis results from Node 2
        signals: Classified citations with weights
        
    Returns:
        InterviewKit object
    """
    provider = get_provider(settings)

    # Identify the weakest dimension to focus the interview on
    dimensions = ["demand", "competition", "viability"]
    weakness_counts = {d: len(analysis.get(d, {}).get("weaknesses", [])) for d in dimensions}
    primary_focus = max(weakness_counts, key=lambda k: weakness_counts[k])
    
    signals_summary = "\n".join([
        f"- [{s.get('source_id')}] Type: {s.get('type')}, "
        f"Content: {(s.get('content') or '')[:100]}..."
        for s in signals[:5]
    ])

    prompt = f"""You are a Master User Researcher specialized in "The Mom Test" methodology.
Your goal is to create a User Interview Toolkit for the business idea: "{title}".

CONTEXT:
{description}

CURRENT FINDINGS:
- Primary Risk Area: {primary_focus.upper()}
- Signals Found:
{signals_summary}

TASK:
Generate an interview toolkit that helps the user validate their riskiest assumptions
through real conversations.

REQUIREMENTS:
1. SCRIPT: 5-7 non-leading questions. Focus on the user's PAST behavior, not their future opinions.
   Include a "Rationale" for each question (e.g. "To test if they currently spend money on X").
2. OUTREACH: 3 templates (LinkedIn, Email, Reddit/Discord) that are short, personal, and NOT salesy.
3. TRACKER: 5-8 column headers for a spreadsheet to track responses.
   (e.g. "Current Solution", "Monthly Pain Score (1-10)", "Budget Owner?").

Return ONLY a JSON object with this structure:
{{
  "script": [
    {{ "question": "...", "rationale": "..." }}
  ],
  "outreach_templates": {{
    "linkedin": "...",
    "email": "...",
    "reddit": "..."
  }},
  "response_tracker": ["Column 1", "Column 2", ...]
}}
"""
    messages = [{"role": "user", "content": prompt}]
    response = await provider.generate(messages, temperature=0.5)
    
    content = response.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    data = json.loads(content)
    
    return InterviewKit(
        script=data.get("script", []),
        outreach_templates=data.get("outreach_templates", {}),
        response_tracker=data.get("response_tracker", [])
    )
