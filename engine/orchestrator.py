"""Thin S-01 orchestrator for lifecycle progression."""

from __future__ import annotations

import logging
import time
from uuid import UUID

from api.config import settings
from db.ideas import get_idea, save_idea
from db.reports import save_report
from db.runs import get_run, transition_run
from engine.analyst import analyze_dimensions
from engine.events import publish_event
from engine.experiments import generate_experiment_kit
from engine.interviewer import generate_interview_kit
from engine.signal_collector import classify_signals, collect_search_signals
from engine.synthesizer import (
    REQUIRES_CITATIONS,
    build_markdown_artifact,
    synthesize_intelligence,
)
from models.idea import ValidationStatus
from models.report import Report
from services.webhooks import dispatch_webhooks

LOGGER = logging.getLogger("engine.orchestrator")


async def execute_run(run_id: UUID) -> None:
    """Advance a run through the minimal happy-path lifecycle."""
    started_at = time.perf_counter()
    run = get_run(run_id)
    if run is None:
        raise ValueError("Run not found")

    LOGGER.info(
        "Run started",
        extra={
            "event": "run_started",
            "extra_fields": {"run_id": str(run_id), "idea_id": str(run.idea_id), "mode": run.mode},
        },
    )

    try:
        transition_run(run_id, "running")
        await publish_event(run_id, "started", {"status": "running"})

        # Collect search signals based on mode
        idea = get_idea(run.idea_id)
        search_results = []
        if idea is not None:
            # Step 1: Collect search signals (Deep if high tier)
            deep_search = run.tier in ("medium", "high")
            if deep_search:
                await publish_event(run_id, "mining", {"label": "Mining pain points"})

            search_results = await collect_search_signals(
                mode=run.mode,
                title=idea.title,
                description=idea.description,
                limit=5,
                deep_search=deep_search,
            )
            await publish_event(
                run_id, "collecting_signals", {"results_count": len(search_results)}
            )
            
            # Step 1.5: Classify and weight signals
            if search_results:
                await publish_event(run_id, "classifying", {"label": "Weighting signals"})
                search_results = await classify_signals(search_results)

        citations = [
            {
                "source_id": f"SRC-{i:03d}",
                "content": res.snippet,
                "url": res.url,
                "type": res.signal_type.value,
                "confidence": res.confidence,
            }
            for i, res in enumerate(search_results, 1)
        ]

        await publish_event(run_id, "analyzing", {"label": "Dimensional sifting"})
        analysis = await analyze_dimensions(
            title=idea.title if idea else "Unknown",
            description=idea.description if idea else "",
            citations=citations,
        )

        await publish_event(run_id, "synthesizing", {"label": "Intelligence synthesis"})
        cards = await synthesize_intelligence(
            title=idea.title if idea else "Unknown",
            description=idea.description if idea else "",
            citations=citations,
            analysis=analysis,
        )

        # Battle Mode (Adversarial Validation) - Node 4
        from engine.battle import BattleOrchestrator

        battle_results = None
        if run.tier in ("medium", "high"):  # Battle mode for higher tiers
            await publish_event(run_id, "battle", {"label": "Bull vs Bear agents"})
            battle_engine = BattleOrchestrator(
                title=idea.title if idea else "Unknown",
                description=idea.description if idea else "",
                signals=citations,
            )
            battle_results = await battle_engine.run_battle()

        # Interview Kit (Node 5)
        interview_kit = None
        if run.tier in ("medium", "high"):
            await publish_event(run_id, "interviewing", {"label": "Drafting interview kit"})
            interview_kit = await generate_interview_kit(
                title=idea.title if idea else "Unknown",
                description=idea.description if idea else "",
                analysis=analysis,
                signals=citations,
            )

        # Experiment Kit (Node 6)
        experiment_kit = None
        if run.tier in ("medium", "high"):
            await publish_event(run_id, "experimenting", {"label": "Designing experiment kit"})
            experiment_kit = await generate_experiment_kit(
                title=idea.title if idea else "Unknown",
                description=idea.description if idea else "",
                analysis_results=analysis,
            )

        # Build and write markdown artifact
        report_text = build_markdown_artifact(
            idea_id=str(run.idea_id),
            cards=cards,
            battle_results=battle_results,
            interview_kit=interview_kit,
            experiment_kit=experiment_kit,
            status=idea.status if idea else ValidationStatus.DESK_RESEARCH,
        )
        artifact_name = f"idea-{run.idea_id}.md"
        artifact_path = settings.app_docs_dir / artifact_name
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(report_text, encoding="utf-8")

        # Step 8: Update Idea Status (Stage Gate)
        if idea and cards:
            # Calculate aggregate score (average of demand, market, competition, viability)
            # These are extracted from synthesized cards.
            scores = [card.score for card in cards if card.type in REQUIRES_CITATIONS]
            if not scores:
                scores = [card.score for card in cards]  # Fallback to all scores
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            new_status = ValidationStatus.DESK_RESEARCH
            if avg_score >= 70:
                new_status = ValidationStatus.EXPERIMENT_READY
            elif avg_score >= 40:
                new_status = ValidationStatus.INTERVIEW_READY
            else:
                new_status = ValidationStatus.PIVOT_RECOMMENDED
            
            if new_status != idea.status:
                idea.status = new_status
                save_idea(idea)
                await publish_event(run_id, "graduated", {"status": new_status.value})

        save_report(
            Report(
                run_id=run_id,
                cards=cards,
                artifact_path=str(artifact_path),
                citations=citations,
                battle_results=battle_results,
                interview_kit=interview_kit,
                experiment_kit=experiment_kit,
            )
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        run.duration_ms = duration_ms
        transition_run(run_id, "succeeded")
        await publish_event(
            run_id, "completed", {"status": "succeeded", "duration_ms": duration_ms}
        )

        # Dispatch webhooks
        await dispatch_webhooks(
            event_type="run.succeeded",
            payload={
                "run_id": str(run_id),
                "idea_id": str(run.idea_id),
                "status": "succeeded",
                "duration_ms": duration_ms,
                "artifact_path": str(artifact_path),
            },
            workspace_id=str(idea.workspace_id) if idea and idea.workspace_id else None,
        )

        LOGGER.info(
            "Run succeeded",
            extra={
                "event": "run_succeeded",
                "extra_fields": {
                    "run_id": str(run_id),
                    "idea_id": str(run.idea_id),
                    "mode": run.mode,
                    "duration_ms": duration_ms,
                },
            },
        )
    except Exception as e:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        run.duration_ms = duration_ms
        transition_run(run_id, "failed", error_code="AE-ENGINE-001")
        await publish_event(run_id, "failed", {"error": str(e), "error_code": "AE-ENGINE-001"})
        LOGGER.error(
            f"Run execution failed: {e}",
            extra={
                "event": "run_failed",
                "extra_fields": {
                    "run_id": str(run_id),
                    "idea_id": str(run.idea_id),
                    "mode": run.mode,
                    "duration_ms": duration_ms,
                    "error": str(e),
                },
            },
            exc_info=True,
        )
        # We don't re-raise here because this is running in a background task
        # and we've already transitioned the state to 'failed'.
