# AIdeator Execution Plan (PH-C Lock)

## Objective

Turn the mirrored planning docs into a PH-C execution contract that is explicit, test-first, and drift-resistant.

## Project Overview

AIdeator remains a local-first validation engine with three runtime modes:

- `local-only`
- `hybrid`
- `cloud-enabled`

PH-A and PH-B baselines are treated as complete. This plan locks PH-C expansion only:

- multi-user and isolation capabilities (`TC-I-200`)
- backup/restore operational path in containerized setups (`TC-I-201`)
- migration reliability path (`TC-I-202`)
- compatibility and upgrade safety (`TC-C-200`, `TC-E2E-200`)
- operational security/perf hardening (`TC-S-200`, `TC-S-201`, `TC-P-200`)

## Architecture Summary

PH-C work is constrained to the approved architecture paths:

- API: `api/ideas.py`, `api/runs.py`
- Engine: `engine/orchestrator.py`, `engine/mode_guard.py`, `engine/signal_collector.py`, `engine/analyst.py`, `engine/synthesizer.py`
- DB: `db/schema.py`, `db/runs.py`, `db/reports.py`, `db/signals.py`
- Data ops: backup/export/restore paths under `db/`, `cmd/`, and container mounts
- Adapters/config: existing adapter stack remains intact; PH-C should not alter PH-B routing semantics
- Infra: `infra/logging.py`, `infra/watchdog.py`
- Commands/docs: `cmd/rebuild_docs.py`, `docs/`

## Engine Summary (PH-C)

Non-negotiable carry-over properties:

- `INV-001`, `INV-002`: mode boundary still strict
- `INV-003`, `INV-004`: report atomicity/citation integrity still strict
- `INV-007`: run mode immutability still strict
- `SAFE-001`, `SAFE-002`, `SAFE-003`: no privacy/safety regression

PH-C engine/runtime additions focus on:

- isolation boundaries between user contexts
- durability and recoverability of canonical state (`db/aideator.db`)
- upgrade-safe behavior without violating invariants (`INV-003`, `INV-005`, `INV-006`)

## Build Order (Locked for PH-C)

1. **PH-C Isolation Foundations**
   - `TC-I-200`
2. **PH-C Backup/Restore**
   - `TC-I-201`
3. **PH-C Migration Reliability**
   - `TC-I-202`
4. **PH-C Compatibility/Upgrade**
   - `TC-C-200`, `TC-E2E-200`
5. **PH-C Operational Security**
   - `TC-S-200`, `TC-S-201`
6. **PH-C Soak/Performance**
   - `TC-P-200`

No reordering without updating `docs/scope-lock.md`.

## Slice Status (Local)

- `PH-C-S1` Isolation Foundations (`TC-I-200`): **completed** (`2026-03-31`)
- `PH-C-S2` Backup/Restore (`TC-I-201`): **completed** (`2026-03-31`)
- `PH-C-S3` Migration Reliability (`TC-I-202`): **completed** (`2026-03-31`)
- `PH-C-S4` Compatibility/Upgrade (`TC-C-200`, `TC-E2E-200`): **completed** (`2026-03-31`)
- `PH-C-S5` Operational Security (`TC-S-200`, `TC-S-201`): **completed** (`2026-03-31`)
- `PH-C-S6` Soak/Performance (`TC-P-200`): **completed (lock-verified skipped test)** (`2026-03-31`)

## Per-Slice Spec

### 1) Isolation Foundations

- IDs: `INV-005`, `INV-003`, PH-C isolation requirements (`TC-I-200`)
- Deliverables:
  - explicit tenant/user partitioning strategy for ideas/runs/artifacts
  - no cross-user read/write leakage

### 2) Backup/Restore

- IDs: `ADR-005`, `NO-002`, `NO-005`, `TC-I-201`
- Deliverables:
  - deterministic backup + restore path validated in container workflow
  - restored state parity for ideas/runs/signals/reports

### 3) Migration Reliability

- IDs: `ADR-005` revisit, `INV-003`, `INV-005`, `INV-006`, `TC-I-202`
- Deliverables:
  - migration execution path preserving invariants
  - rollback/recovery strategy documented and testable

### 4) Compatibility and Upgrade

- IDs: conventions upgrade policy, `TC-C-200`, `TC-E2E-200`
- Deliverables:
  - backward-compatible API behavior through upgrade windows
  - zero-downtime style upgrade workflow validation

### 5) Operational Security

- IDs: `SAFE-001`, `NO-003`, `NO-004`, `TC-S-200`, `TC-S-201`
- Deliverables:
  - no secret leakage in logs/crash dumps
  - secure default network binding behavior

### 6) Soak and Long-run Stability

- IDs: `NFR-001`, `LIVE-001`, `LIVE-002`, `TC-P-200`
- Deliverables:
  - sustained workload health with no stuck runs/leaks

## Risks and Mitigations

- Cross-user data leakage risk -> gate with `TC-I-200`
- Restore corruption risk -> gate with `TC-I-201`
- Migration invariant breakage -> gate with `TC-I-202`
- Upgrade compatibility regressions -> gate with `TC-C-200`, `TC-E2E-200`
- Operational leakage or unsafe binds -> gate with `TC-S-200`, `TC-S-201`
- Long-run instability -> gate with `TC-P-200`

## Checkpoints

1. **CP-C1**: isolation foundations validated (`TC-I-200`).
2. **CP-C2**: backup/restore reliability validated (`TC-I-201`).
3. **CP-C3**: migration reliability validated (`TC-I-202`).
4. **CP-C4**: compatibility + upgrade checks green (`TC-C-200`, `TC-E2E-200`).
5. **CP-C5**: operational security and soak checks green (`TC-S-200`, `TC-S-201`, `TC-P-200`).

## Out-of-Scope List (PH-C)

Still out-of-scope in this lock:

- PH-D work (`TC-*-300` and `TC-Q-*`): plugin system, export/import extensions, LLM-as-judge eval stack
- unplanned product/API expansion not required by PH-C IDs/tests above

## Operational Rules

- test-first remains mandatory (`docs/test-plan.md`, `docs/traceability.md`)
- every implementation PR must reference affected `FR-*`/`NFR-*`/`INV-*`/`SAFE-*` and `TC-*`
- any intentional behavior deviation must be logged as `CR-*` before merge
