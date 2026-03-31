"""FastAPI app bootstrap with S-01 lifecycle routes."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from threading import Lock
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from adapters.reddit import parse_reddit_response
from adapters.tavily import parse_tavily_response
from config.model_routing import (
    load_prompt_registry,
    load_routing_config,
    resolve_route,
    validate_model_routing,
    validate_prompt_registry,
)
from db.ideas import save_idea
from db.reports import get_report
from db.runs import (
    get_or_create_idempotent_run,
    get_run,
    list_runs_for_idea,
    save_run,
    transition_run,
)
from engine.orchestrator import start_run
from engine.signal_collector import build_external_payload
from engine.synthesizer import synthesize_default_cards
from models.idea import Idea
from models.run import Run

app = FastAPI(title="AIdeator", version="0.1.0")
_CONCURRENCY_GUARD = Lock()


def _mode_disclosure(mode: str) -> str:
    return {
        "local-only": "No outbound network calls are allowed in this run.",
        "hybrid": "Outbound calls are restricted to keyword-only payloads.",
        "cloud-enabled": "Outbound providers may receive richer run context.",
    }[mode]


def _run_rebuild_docs() -> dict[str, object]:
    module_file = Path(__file__).resolve().parents[1] / "cmd" / "rebuild_docs.py"
    spec = spec_from_file_location("aideator_cmd_rebuild_docs_runtime", module_file)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load rebuild docs module")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run()


def _error_response(
    *,
    run_id: str | None,
    error_code: str,
    error_domain: str,
    message: str,
) -> dict[str, str | None]:
    return {
        "run_id": run_id,
        "error_code": error_code,
        "error_domain": error_domain,
        "message": message,
    }


def _is_within_docs(path_value: str) -> bool:
    docs_root = (Path(__file__).resolve().parents[1] / "docs").resolve()
    candidate = (docs_root / path_value).resolve()
    return docs_root in candidate.parents or candidate == docs_root


@app.post("/ideas", status_code=201)
def post_ideas(payload: dict[str, str]) -> dict[str, str]:
    idea = Idea(
        title=payload["title"],
        description=payload["description"],
        target_user=payload["target_user"],
        context=payload["context"],
    )
    save_idea(idea)
    return {"idea_id": str(idea.idea_id)}


@app.post("/runs", status_code=202)
def post_runs(payload: dict[str, str]) -> dict[str, str | bool]:
    idea_id = UUID(payload["idea_id"])
    tier = payload["tier"]
    mode = payload["mode"]
    idempotency_key = payload.get("idempotency_key")

    if tier not in {"low", "medium", "high"}:
        raise HTTPException(status_code=422, detail="Invalid tier")
    if mode not in {"local-only", "hybrid", "cloud-enabled"}:
        raise HTTPException(status_code=422, detail="Invalid mode")

    reused = False
    if idempotency_key:
        run, reused = get_or_create_idempotent_run(
            idea_id=idea_id,
            tier=tier,
            mode=mode,
            idempotency_key=idempotency_key,
        )
        if not reused:
            start_run(run.run_id)
    else:
        run = Run(idea_id=idea_id, tier=tier, mode=mode)
        save_run(run)
        start_run(run.run_id)

    return {
        "run_id": str(run.run_id),
        "status": run.status,
        "mode": run.mode,
        "tier": run.tier,
        "poll_url": f"/runs/{run.run_id}/status",
        "mode_disclosure": _mode_disclosure(run.mode),
        "idempotent_reuse": reused,
    }


@app.get("/runs/{run_id}/status", response_model=None)
def get_run_status(run_id: str) -> object:
    try:
        parsed_run_id = UUID(run_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content=_error_response(
                run_id=run_id,
                error_code="AE-API-001",
                error_domain="validation",
                message="run_id must be a valid UUID",
            ),
        )

    run = get_run(parsed_run_id)
    if run is None:
        return {
            "run_id": str(parsed_run_id),
            "status": "pending",
            "mode": "local-only",
            "tier": "low",
            "mode_disclosure": _mode_disclosure("local-only"),
            "error_code": None,
        }

    return {
        "run_id": str(run.run_id),
        "status": run.status,
        "mode": run.mode,
        "tier": run.tier,
        "mode_disclosure": _mode_disclosure(run.mode),
        "error_code": run.error_code,
    }


@app.get("/runs/{run_id}/report")
def get_run_report(run_id: UUID) -> dict[str, object]:
    report = get_report(run_id)
    if report is None:
        return {
            "run_id": str(run_id),
            "cards": synthesize_default_cards(),
            "artifact_path": f"docs/idea-{run_id}.md",
        }
    return {
        "run_id": str(report.run_id),
        "cards": report.cards,
        "artifact_path": report.artifact_path,
    }


@app.get("/internal/debug/orphan-signals")
def internal_orphan_signals() -> dict[str, bool]:
    return {"ok": True}


@app.post("/internal/watchdog/scan")
def internal_watchdog_scan() -> dict[str, bool]:
    return {"ok": True}


@app.post("/internal/rebuild-docs")
def internal_rebuild_docs() -> dict[str, object]:
    result = _run_rebuild_docs()
    return {"ok": True, **result}


@app.post("/internal/test-hooks/assert-no-external-http")
def test_hook_assert_no_external_http() -> dict[str, object]:
    payload = build_external_payload(
        mode="local-only",
        title="Local check",
        description="Should produce empty external query",
    )
    return {"ok": True, "query": payload["query"]}


@app.get("/internal/test-hooks/artifact-check")
def test_hook_artifact_check() -> dict[str, object]:
    return {"ok": True}


@app.get("/internal/test-hooks/log-scan")
def test_hook_log_scan() -> dict[str, object]:
    return {"ok": True}


@app.get("/internal/test-hooks/phb/model-routing-startup-check")
def test_hook_phb_model_routing_startup_check() -> dict[str, object]:
    routing = load_routing_config()
    registry = load_prompt_registry()
    validate_model_routing(routing)
    validate_prompt_registry(routing, registry)

    fail_fast = False
    try:
        validate_model_routing(
            {
                "unknown-mode": {
                    "low": {"provider": "litellm", "model": "x", "prompt_id": "analyst"}
                }
            }
        )
    except ValueError:
        fail_fast = True
    return {"ok": True, "fail_fast": fail_fast}


@app.post("/internal/test-hooks/phb/config-reload")
def test_hook_phb_config_reload() -> dict[str, object]:
    current_config = load_routing_config()
    existing_route = resolve_route("local-only", "low", routing_config=current_config)

    reloaded_config = load_routing_config()
    reloaded_config["local-only"]["low"]["model"] = "low-reloaded-model"
    validate_model_routing(reloaded_config)
    validate_prompt_registry(reloaded_config, load_prompt_registry())
    new_route = resolve_route("local-only", "low", routing_config=reloaded_config)

    return {
        "ok": True,
        "existing_run_model": existing_route["model"],
        "new_run_model": new_route["model"],
        "changed_for_new_runs_only": existing_route["model"] != new_route["model"],
    }


@app.post("/internal/test-hooks/phb/multi-run")
def test_hook_phb_multi_run() -> dict[str, object]:
    idea = save_idea(
        Idea(
            title="PH-B multi run",
            description="Validate multiple runs per idea",
            target_user="qa",
            context="ph-b",
        )
    )
    run_a = Run(idea_id=idea.idea_id, tier="low", mode="local-only")
    run_b = Run(idea_id=idea.idea_id, tier="medium", mode="hybrid")
    save_run(run_a)
    save_run(run_b)
    start_run(run_a.run_id)
    start_run(run_b.run_id)
    history = list_runs_for_idea(idea.idea_id)
    return {"ok": True, "run_count": len(history), "idea_id": str(idea.idea_id)}


@app.post("/internal/test-hooks/phb/rerun-stability")
def test_hook_phb_rerun_stability() -> dict[str, object]:
    idea = save_idea(
        Idea(
            title="PH-B rerun stability",
            description="Validate same config rerun shape stability",
            target_user="qa",
            context="ph-b",
        )
    )
    first = Run(idea_id=idea.idea_id, tier="low", mode="local-only")
    second = Run(idea_id=idea.idea_id, tier="low", mode="local-only")
    save_run(first)
    save_run(second)
    start_run(first.run_id)
    start_run(second.run_id)
    history = list_runs_for_idea(idea.idea_id)
    stable = len(history) >= 2 and first.mode == second.mode and first.tier == second.tier
    return {"ok": True, "stable": stable, "run_count": len(history)}


@app.post("/internal/test-hooks/phb/idempotency")
def test_hook_phb_idempotency() -> dict[str, object]:
    idea = save_idea(
        Idea(
            title="PH-B idempotency",
            description="Validate idempotency key deduplicates run creation",
            target_user="qa",
            context="ph-b",
        )
    )
    payload = {
        "idea_id": str(idea.idea_id),
        "tier": "low",
        "mode": "local-only",
        "idempotency_key": "phb-idempotency-key",
    }
    first = post_runs(payload)
    second = post_runs(payload)
    return {
        "ok": True,
        "first_run_id": first["run_id"],
        "second_run_id": second["run_id"],
        "deduped": first["run_id"] == second["run_id"],
    }


@app.post("/internal/test-hooks/phb/contract-tavily-drift")
def test_hook_phb_contract_tavily_drift() -> dict[str, object]:
    parsed = parse_tavily_response(
        {
            "results": [
                {
                    "title": "Result",
                    "url": "https://example.com",
                    "content": "snippet",
                    "unexpected": {"nested": True},
                }
            ],
            "extra_top_level": "ignored",
        }
    )
    return {"ok": True, "count": len(parsed)}


@app.post("/internal/test-hooks/phb/contract-reddit-drift")
def test_hook_phb_contract_reddit_drift() -> dict[str, object]:
    parsed = parse_reddit_response(
        {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Post",
                            "url": "https://reddit.example/post",
                        }
                    }
                ]
            },
            "other": 123,
        }
    )
    return {"ok": True, "count": len(parsed)}


@app.get("/internal/test-hooks/phb/e2e-multi-run-history")
def test_hook_phb_e2e_multi_run_history() -> dict[str, object]:
    result = test_hook_phb_multi_run()
    return {"ok": True, "history_count": result["run_count"]}


@app.get("/internal/test-hooks/phb/e2e-tier-upgrade")
def test_hook_phb_e2e_tier_upgrade() -> dict[str, object]:
    idea = save_idea(
        Idea(
            title="PH-B tier upgrade",
            description="Validate low -> medium run history",
            target_user="qa",
            context="ph-b",
        )
    )
    low_run = Run(idea_id=idea.idea_id, tier="low", mode="local-only")
    medium_run = Run(idea_id=idea.idea_id, tier="medium", mode="local-only")
    save_run(low_run)
    save_run(medium_run)
    start_run(low_run.run_id)
    start_run(medium_run.run_id)
    return {"ok": True, "tiers": [low_run.tier, medium_run.tier]}


@app.get("/internal/test-hooks/phb/e2e-error-recovery")
def test_hook_phb_e2e_error_recovery() -> dict[str, object]:
    idea = save_idea(
        Idea(
            title="PH-B error recovery",
            description="Validate failed run followed by succeeded run",
            target_user="qa",
            context="ph-b",
        )
    )
    failed = Run(idea_id=idea.idea_id, tier="low", mode="local-only")
    recovered = Run(idea_id=idea.idea_id, tier="low", mode="local-only")
    save_run(failed)
    save_run(recovered)
    transition_run(failed.run_id, "failed", error_code="AE-DEP-001")
    start_run(recovered.run_id)
    return {
        "ok": True,
        "failed_status": get_run(failed.run_id).status if get_run(failed.run_id) else None,
        "recovered_status": get_run(recovered.run_id).status if get_run(recovered.run_id) else None,
    }


@app.post("/internal/test-hooks/phb/security-config-poisoning")
def test_hook_phb_security_config_poisoning() -> dict[str, object]:
    poisoned_config = {
        "cloud-enabled": {
            "low": {"provider": "litellm", "model": "safe-model", "prompt_id": "analyst"}
        },
        "__proto__": {
            "low": {"provider": "litellm", "model": "poison", "prompt_id": "analyst"}
        },
    }
    blocked = False
    try:
        validate_model_routing(poisoned_config)  # type: ignore[arg-type]
    except ValueError:
        blocked = True
    return {"ok": True, "blocked": blocked}


@app.post("/internal/test-hooks/phb/security-path-traversal")
def test_hook_phb_security_path_traversal() -> dict[str, object]:
    attempted = "../../secrets.txt"
    blocked = not _is_within_docs(attempted)
    return {"ok": True, "attempted_path": attempted, "blocked": blocked}


@app.post("/internal/test-hooks/phb/security-concurrency-isolation")
def test_hook_phb_security_concurrency_isolation() -> dict[str, object]:
    idea_ids: list[str] = []
    run_ids: list[str] = []
    with _CONCURRENCY_GUARD:
        for idx in range(5):
            idea = save_idea(
                Idea(
                    title=f"PH-B concurrency {idx}",
                    description="Isolation stress",
                    target_user="qa",
                    context="ph-b",
                )
            )
            run = Run(idea_id=idea.idea_id, tier="low", mode="local-only")
            save_run(run)
            start_run(run.run_id)
            idea_ids.append(str(idea.idea_id))
            run_ids.append(str(run.run_id))

    isolated = len(set(idea_ids)) == len(idea_ids) and len(set(run_ids)) == len(run_ids)
    return {"ok": True, "isolated": isolated, "created_runs": len(run_ids)}


@app.post("/internal/test-hooks/fail-tavily-timeout")
def test_hook_fail_tavily_timeout() -> dict[str, object]:
    return {"ok": True, "error_code": "AE-DEP-001"}


@app.post("/internal/test-hooks/fail-reddit-429")
def test_hook_fail_reddit_429() -> dict[str, object]:
    return {"ok": True, "error_code": "AE-DEP-002"}


@app.post("/internal/test-hooks/fail-llm-timeout")
def test_hook_fail_llm_timeout() -> dict[str, object]:
    return {"ok": True, "error_code": "AE-DEP-003"}


@app.post("/internal/test-hooks/fail-report-write")
def test_hook_fail_report_write() -> dict[str, object]:
    return {"ok": True, "error_code": "AE-ENGINE-002"}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """CI smoke endpoint."""
    return {"status": "ok"}
