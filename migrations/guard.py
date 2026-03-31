"""PH-C migration invariant guard helpers."""

from __future__ import annotations

from typing import Any


def assert_invariants(snapshot: dict[str, Any]) -> dict[str, int]:
    ideas = snapshot.get("ideas", [])
    runs_payload = snapshot.get("runs", {})
    signals = snapshot.get("signals", {})
    reports = snapshot.get("reports", [])

    if not isinstance(ideas, list):
        raise ValueError("ideas snapshot must be a list")
    if not isinstance(runs_payload, dict):
        raise ValueError("runs snapshot must be a dict")
    if not isinstance(signals, dict):
        raise ValueError("signals snapshot must be a dict")
    if not isinstance(reports, list):
        raise ValueError("reports snapshot must be a list")

    runs = runs_payload.get("runs", [])
    if not isinstance(runs, list):
        raise ValueError("runs.runs snapshot must be a list")

    idea_ids = {str(item.get("idea_id")) for item in ideas if isinstance(item, dict)}
    run_ids = {str(item.get("run_id")) for item in runs if isinstance(item, dict)}

    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("invalid run row payload")
        if str(run.get("idea_id")) not in idea_ids:
            raise ValueError("orphan run found: run references unknown idea")
        if str(run.get("status")) not in {"pending", "running", "succeeded", "failed"}:
            raise ValueError("invalid run status found")

    for report in reports:
        if not isinstance(report, dict):
            raise ValueError("invalid report row payload")
        if str(report.get("run_id")) not in run_ids:
            raise ValueError("orphan report found: report references unknown run")

    for run_id in signals:
        if str(run_id) not in run_ids:
            raise ValueError("orphan signal found: signal references unknown run")

    return {
        "ideas": len(idea_ids),
        "runs": len(run_ids),
        "signals": len(signals),
        "reports": len(reports),
    }


def verify_invariants_after_migration(
    *, before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    before_counts = assert_invariants(before)
    after_counts = assert_invariants(after)
    if before_counts != after_counts:
        raise ValueError("migration changed entity counts")
    return {"ok": True, "before_counts": before_counts, "after_counts": after_counts}
