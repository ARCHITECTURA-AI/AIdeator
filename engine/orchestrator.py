"""Thin S-01 orchestrator for lifecycle progression."""

from __future__ import annotations

import logging
import time
from uuid import UUID

from api.config import settings
from db.ideas import get_idea
from db.reports import save_report
from db.runs import get_run, transition_run
from engine.analyst import analyze_dimensions
from engine.events import publish_event
from engine.signal_collector import collect_search_signals
from engine.synthesizer import build_markdown_artifact, synthesize_intelligence
from models.report import Report

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
            search_results = await collect_search_signals(
                mode=run.mode,
                title=idea.title,
                description=idea.description,
                limit=5,
            )
            await publish_event(
                run_id, 
                "collecting_signals", 
                {"results_count": len(search_results)}
            )

        citations = [
            {
                "source_id": f"SRC-{i:03d}",
                "content": res.snippet,
                "url": res.url,
            }
            for i, res in enumerate(search_results, 1)
        ]
        
        await publish_event(run_id, "analyzing", {"label": "Dimensional sifting"})
        analysis = await analyze_dimensions(
            title=idea.title if idea else "Unknown",
            description=idea.description if idea else "",
            citations=citations
        )
        
        await publish_event(run_id, "synthesizing", {"label": "Intelligence synthesis"})
        cards = await synthesize_intelligence(
            title=idea.title if idea else "Unknown",
            description=idea.description if idea else "",
            citations=citations,
            analysis=analysis
        )
        
        # Build and write markdown artifact
        report_text = build_markdown_artifact(idea_id=str(run.idea_id), cards=cards)
        artifact_name = f"idea-{run.idea_id}.md"
        artifact_path = settings.app_docs_dir / artifact_name
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(report_text, encoding="utf-8")

        save_report(
            Report(
                run_id=run_id,
                cards=cards,
                artifact_path=str(artifact_path),
                citations=citations,
            )
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        run.duration_ms = duration_ms
        transition_run(run_id, "succeeded")
        await publish_event(run_id, "completed", {"status": "succeeded", "duration_ms": duration_ms})
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
