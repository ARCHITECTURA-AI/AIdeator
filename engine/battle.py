"""Adversarial validation (Battle Mode) orchestrator."""

from __future__ import annotations

import json
import logging
from typing import Any

from aideator.llm.registry import get_provider
from api.config import settings

LOGGER = logging.getLogger("engine.battle")


class BattleOrchestrator:
    """Orchestrates Bull and Bear agents for adversarial analysis."""

    def __init__(self, title: str, description: str, signals: list[dict[str, Any]]):
        self.title = title
        self.description = description
        self.signals = signals
        self.provider = get_provider(settings)

    async def run_battle(self) -> dict[str, Any]:
        """Run Bull vs Bear analysis."""
        signals_text = "\n".join([f"- {s['content']} (Source: {s['url']})" for s in self.signals])

        # 1. The Bull (Optimist)
        bull_prompt = f"""You are 'The Bull'—a relentless growth optimist and venture partner.
Your goal is to find the maximum potential in the business idea: "{self.title}".

DESCRIPTION:
{self.description}

SIGNALS:
{signals_text}

Task:
Identify the biggest growth levers, market tailwinds, and why this could be a 100x opportunity. 
Focus on:
- Unmet demand signals.
- Scalability shortcuts.
- Potential for market dominance.

Return a concise paragraph of 3-4 sentences.
"""
        bull_res = await self.provider.generate([{"role": "user", "content": bull_prompt}])
        bull_text = bull_res.content.strip()

        # 2. The Bear (Skeptic)
        bear_prompt = f"""You are 'The Bear'—a cynical risk manager and veteran short-seller.
Your goal is to find every reason why the business idea "{self.title}" will fail.

DESCRIPTION:
{self.description}

SIGNALS:
{signals_text}

Task:
Identify the fatal flaws, competitive moats of incumbents, and execution risks.
Focus on:
- Churn risks and high CAC.
- Regulatory or technical hurdles.
- Why incumbents will crush this.

Return a concise paragraph of 3-4 sentences.
"""
        bear_res = await self.provider.generate([{"role": "user", "content": bear_prompt}])
        bear_text = bear_res.content.strip()

        # 3. Synthesis (The Counter-Point)
        synthesis_prompt = f"""You are a Strategic Arbitrator.
Synthesize the conflict between the following two perspectives into a 'Counter-Point' section.

BULL PERSPECTIVE:
{bull_text}

BEAR PERSPECTIVE:
{bear_text}

Task:
Create a 'Battle Report' that highlights the core tension.
What is the one thing this idea's success hinges on?
Return a JSON object:
{{
  "bull_case": "{bull_text}",
  "bear_case": "{bear_text}",
  "the_hinge": "1-2 sentences on the critical dependency"
}}
"""
        synth_res = await self.provider.generate([{"role": "user", "content": synthesis_prompt}])
        try:
            content = synth_res.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            LOGGER.error(f"Battle synthesis failed: {e}")
            return {
                "bull_case": bull_text,
                "bear_case": bear_text,
                "the_hinge": (
                    "Success hinges on balancing aggressive growth with "
                    "operational risk mitigation."
                ),
            }
