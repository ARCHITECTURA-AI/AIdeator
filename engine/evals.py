"""PH-D eval budget and semantic quality helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvalBudgetDecision:
    allowed: bool
    reason: str
    remaining_budget_usd: float


def check_eval_budget(
    *,
    evals_enabled: bool,
    estimated_cost_usd: float,
    budget_usd: float,
) -> EvalBudgetDecision:
    """Return a deterministic budget decision without side effects."""
    remaining = round(budget_usd - estimated_cost_usd, 6)
    if not evals_enabled:
        return EvalBudgetDecision(
            allowed=False,
            reason="evals_disabled",
            remaining_budget_usd=max(remaining, 0.0),
        )
    if estimated_cost_usd > budget_usd:
        return EvalBudgetDecision(
            allowed=False,
            reason="budget_exceeded",
            remaining_budget_usd=max(remaining, 0.0),
        )
    return EvalBudgetDecision(
        allowed=True,
        reason="within_budget",
        remaining_budget_usd=max(remaining, 0.0),
    )


def enforce_eval_budget(
    *,
    evals_enabled: bool,
    estimated_cost_usd: float,
    budget_usd: float,
) -> bool:
    """Boolean guard used by runtime hooks before running evals."""
    return check_eval_budget(
        evals_enabled=evals_enabled,
        estimated_cost_usd=estimated_cost_usd,
        budget_usd=budget_usd,
    ).allowed


def evaluate_card_semantics(
    *,
    summary: str,
    citation_count: int,
    threshold: float = 0.55,
) -> dict[str, float | bool]:
    """Compute a lightweight semantic quality proxy score for card content."""
    summary_words = len([word for word in summary.split() if word.strip()])
    summary_component = min(summary_words / 20.0, 1.0)
    citation_component = min(float(citation_count), 2.0) / 2.0
    score = round((summary_component * 0.6) + (citation_component * 0.4), 3)
    return {"score": score, "pass": score >= threshold}


def evaluate_notes_actionability(
    *,
    notes_markdown: str,
    threshold: float = 0.55,
) -> dict[str, float | bool]:
    """Score actionability by counting clear imperative next-step markers."""
    lower_notes = notes_markdown.lower()
    action_markers = ("must", "should", "next", "implement", "verify", "run", "measure")
    marker_hits = sum(1 for marker in action_markers if marker in lower_notes)
    score = round(min(marker_hits / 5.0, 1.0), 3)
    return {"score": score, "pass": score >= threshold}
