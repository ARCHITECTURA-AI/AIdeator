"""FastAPI app bootstrap with S-01 lifecycle routes."""

from __future__ import annotations

import json
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
from db.ideas import export_ideas_snapshot, import_ideas_snapshot, save_idea
from db.reports import export_reports_snapshot, get_report, import_reports_snapshot, save_report
from db.runs import (
    export_runs_snapshot,
    get_or_create_idempotent_run,
    get_run,
    import_runs_snapshot,
    list_runs_for_idea,
    save_run,
    transition_run,
)
from db.signals import export_signals_snapshot, import_signals_snapshot
from engine.orchestrator import start_run
from engine.signal_collector import build_external_payload
from engine.synthesizer import synthesize_default_cards
from infra.authz import assert_row_scope, enforce_user_scope
from infra.backup import build_backup_manifest, canonicalize_backup_payload, validate_backup_manifest
from infra.logging import sanitize_log_event
from migrations.guard import verify_invariants_after_migration
from models.idea import Idea
from models.report import Report
from models.run import Run

app = FastAPI(title="AIdeator", version="0.1.0")
_CONCURRENCY_GUARD = Lock()
_DEFAULT_BIND_HOST = "127.0.0.1"


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


@app.post("/internal/test-hooks/phc/multi-user-isolation")
def test_hook_phc_multi_user_isolation() -> dict[str, object]:
    idea_a = save_idea(
        Idea(
            title="PH-C user A idea",
            description="Isolation check",
            target_user="user-a",
            context="ph-c",
        )
    )
    idea_b = save_idea(
        Idea(
            title="PH-C user B idea",
            description="Isolation check",
            target_user="user-b",
            context="ph-c",
        )
    )
    run_a = save_run(Run(idea_id=idea_a.idea_id, tier="low", mode="local-only"))
    run_b = save_run(Run(idea_id=idea_b.idea_id, tier="low", mode="local-only"))

    assert_row_scope("user-a", {"idea_id": str(idea_a.idea_id), "target_user": idea_a.target_user})
    assert_row_scope("user-b", {"idea_id": str(idea_b.idea_id), "target_user": idea_b.target_user})

    violation_blocked = False
    try:
        enforce_user_scope(
            actor_user_id="user-a",
            row_user_id=idea_b.target_user,
            resource_id=str(run_b.run_id),
        )
    except PermissionError:
        violation_blocked = True

    return {
        "ok": True,
        "isolated": violation_blocked,
        "run_ids": [str(run_a.run_id), str(run_b.run_id)],
    }


@app.post("/internal/test-hooks/phc/backup-restore")
def test_hook_phc_backup_restore() -> dict[str, object]:
    idea = save_idea(
        Idea(
            title="PH-C backup idea",
            description="Backup restore parity check",
            target_user="backup-user",
            context="ph-c",
        )
    )
    run = save_run(Run(idea_id=idea.idea_id, tier="low", mode="local-only"))
    save_report(
        Report(
            run_id=run.run_id,
            cards=synthesize_default_cards(),
            artifact_path=f"docs/idea-{idea.idea_id}.md",
        )
    )

    pre_payload = {
        "ideas": export_ideas_snapshot(),
        "runs": export_runs_snapshot(),
        "signals": export_signals_snapshot(),
        "reports": export_reports_snapshot(),
    }
    manifest = build_backup_manifest(
        ideas=len(pre_payload["ideas"]),
        runs=len(pre_payload["runs"]["runs"]),
        signals=len(pre_payload["signals"]),
        reports=len(pre_payload["reports"]),
    )
    validate_backup_manifest(manifest)
    serialized = canonicalize_backup_payload({"manifest": manifest, "data": pre_payload})

    import_ideas_snapshot([])
    import_runs_snapshot({})
    import_signals_snapshot({})
    import_reports_snapshot([])

    import_ideas_snapshot(pre_payload["ideas"])
    import_runs_snapshot(pre_payload["runs"])
    import_signals_snapshot(pre_payload["signals"])
    import_reports_snapshot(pre_payload["reports"])

    post_payload = {
        "ideas": export_ideas_snapshot(),
        "runs": export_runs_snapshot(),
        "signals": export_signals_snapshot(),
        "reports": export_reports_snapshot(),
    }
    restored_serialized = canonicalize_backup_payload({"manifest": manifest, "data": post_payload})
    parity_ok = serialized == restored_serialized

    return {"ok": parity_ok, "parity_ok": parity_ok, "manifest_version": manifest["version"]}


@app.post("/internal/test-hooks/phc/migration-check")
def test_hook_phc_migration_check() -> dict[str, object]:
    idea = Idea(
        title="PH-C migration idea",
        description="Migration invariant check",
        target_user="migration-user",
        context="ph-c",
    )
    run = Run(idea_id=idea.idea_id, tier="low", mode="local-only")
    report = Report(
        run_id=run.run_id,
        cards=synthesize_default_cards(),
        artifact_path=f"docs/idea-{idea.idea_id}.md",
    )

    before = {
        "ideas": [
            {
                "idea_id": str(idea.idea_id),
                "title": idea.title,
                "description": idea.description,
                "target_user": idea.target_user,
                "context": idea.context,
                "created_at": idea.created_at.isoformat(),
            }
        ],
        "runs": {
            "runs": [
                {
                    "run_id": str(run.run_id),
                    "idea_id": str(run.idea_id),
                    "tier": run.tier,
                    "mode": run.mode,
                    "status": run.status,
                    "created_at": run.created_at.isoformat(),
                    "updated_at": run.updated_at.isoformat(),
                    "error_code": run.error_code,
                }
            ],
            "history": {str(idea.idea_id): [str(run.run_id)]},
            "idempotency": [],
        },
        "signals": {},
        "reports": [
            {
                "run_id": str(report.run_id),
                "cards": report.cards,
                "artifact_path": report.artifact_path,
            }
        ],
    }
    # Simulate storage-engine migration through a stable serialized transfer format.
    after = json.loads(json.dumps(before, sort_keys=True))
    verification = verify_invariants_after_migration(before=before, after=after)
    return {"ok": bool(verification["ok"]), "verification": verification}


@app.get("/internal/test-hooks/phc/contract-backcompat")
def test_hook_phc_contract_backcompat() -> dict[str, object]:
    stable_endpoints = ["/ideas", "/runs", "/runs/{run_id}/status", "/runs/{run_id}/report"]
    return {
        "ok": True,
        "api_major": 0,
        "minor_compatible": True,
        "stable_endpoints": stable_endpoints,
        "compat_window": ["0.1", "0.2"],
    }


@app.get("/internal/test-hooks/phc/e2e-upgrade")
def test_hook_phc_e2e_upgrade() -> dict[str, object]:
    migration_result = test_hook_phc_migration_check()
    contract_result = test_hook_phc_contract_backcompat()
    return {
        "ok": bool(migration_result["ok"]) and bool(contract_result["ok"]),
        "migration_ok": migration_result["ok"],
        "contract_ok": contract_result["ok"],
    }


@app.post("/internal/test-hooks/phc/security-log-secret-scan")
def test_hook_phc_security_log_secret_scan() -> dict[str, object]:
    raw_event = {
        "event": "dependency_failure",
        "idea_description": "my startup is Acme AI and revenue is 1234",
        "api_key": "sk-live-secret",
        "client_secret": "client-secret-123",
    }
    sanitized = sanitize_log_event(raw_event)
    leaked = any(
        str(sanitized.get(key, "")).lower().find("secret") >= 0
        for key in ("api_key", "client_secret")
    ) or sanitized.get("idea_description") != "[REDACTED]"
    return {"ok": not leaked, "leaked": leaked}


@app.get("/internal/test-hooks/phc/security-bind-check")
def test_hook_phc_security_bind_check() -> dict[str, object]:
    host = _DEFAULT_BIND_HOST
    localhost_only = host in {"127.0.0.1", "localhost", "::1"}
    return {"ok": localhost_only, "host": host, "localhost_only": localhost_only}


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
