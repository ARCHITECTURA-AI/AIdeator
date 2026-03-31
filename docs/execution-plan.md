# AIdeator Execution Plan (PH-D Lock)

## Objective

Turn the mirrored planning docs into a PH-D execution contract that is explicit, test-first, and drift-resistant.

## Project Overview

AIdeator remains a local-first validation engine with three runtime modes:

- `local-only`
- `hybrid`
- `cloud-enabled`

PH-A, PH-B, and PH-C baselines are treated as complete. This plan locks PH-D expansion only:

- plugin isolation and extension boundaries (`TC-I-300`, `TC-C-300`, `TC-S-300`)
- additional signal source mode compliance (`TC-I-301`)
- cross-version export/import integrity (`TC-E2E-300`)
- eval cost/runtime budget control (`TC-P-300`)
- semantic quality gates (`TC-Q-300`, `TC-Q-301`, `TC-Q-302`)

## Architecture Summary

PH-D work is constrained to the approved architecture paths:

- API: `api/ideas.py`, `api/runs.py`
- Engine: `engine/orchestrator.py`, `engine/mode_guard.py`, `engine/signal_collector.py`, `engine/analyst.py`, `engine/synthesizer.py`
- DB: `db/schema.py`, `db/runs.py`, `db/reports.py`, `db/signals.py`
- Data ops: export/import paths under `db/`, `cmd/`, and docs artifacts
- Adapters/config: plugin/source extension points must remain ModeGuard-mediated
- Infra: `infra/logging.py`, `infra/watchdog.py`
- Commands/docs: `cmd/rebuild_docs.py`, `docs/`

## Engine Summary (PH-D)

Non-negotiable carry-over properties:

- `INV-001`, `INV-002`: mode boundary still strict
- `INV-003`, `INV-004`: report atomicity/citation integrity still strict
- `INV-007`: run mode immutability still strict
- `SAFE-001`, `SAFE-002`, `SAFE-003`: no privacy/safety regression

PH-D engine/runtime additions focus on:

- plugin sandbox boundaries and safe extension interfaces
- additional source adapters without violating `INV-001` / `INV-002`
- quality-eval flow and budget controls without regressing existing invariants

## Build Order (Locked for PH-D)

1. **PH-D Plugin Isolation Foundations**
   - `TC-I-300`, `TC-C-300`, `TC-S-300`
2. **PH-D Source Expansion Boundaries**
   - `TC-I-301`
3. **PH-D Export/Import Compatibility**
   - `TC-E2E-300`
4. **PH-D Eval Cost and Runtime Control**
   - `TC-P-300`
5. **PH-D Semantic Quality Gates**
   - `TC-Q-300`, `TC-Q-301`, `TC-Q-302`

No reordering without updating `docs/scope-lock.md`.

## Slice Status (Local)

- `PH-D-S1` Plugin Isolation Foundations (`TC-I-300`, `TC-C-300`, `TC-S-300`): **completed**
- `PH-D-S2` Source Expansion Boundaries (`TC-I-301`): **completed**
- `PH-D-S3` Export/Import Compatibility (`TC-E2E-300`): **completed**
- `PH-D-S4` Eval Cost and Runtime Control (`TC-P-300`): **completed (budget guards implemented; perf test remains lock-skipped)**
- `PH-D-S5` Semantic Quality Gates (`TC-Q-300`, `TC-Q-301`, `TC-Q-302`): **completed**

## Per-Slice Spec

### 1) Plugin Isolation Foundations

- IDs: `SAFE-005`, `NO-008`, PH-D plugin contracts (`TC-I-300`, `TC-C-300`, `TC-S-300`)
- Deliverables:
  - explicit plugin API boundary
  - plugin isolation from direct DB writes
  - sandboxed file/network access behavior

### 2) Source Expansion Boundaries

- IDs: `INV-001`, `INV-002`, `ADR-001`, `TC-I-301`
- Deliverables:
  - additional source adapters run through ModeGuard
  - hybrid/local-only boundary guarantees preserved

### 3) Export/Import Compatibility

- IDs: `NO-005`, conventions export policy, `TC-E2E-300`
- Deliverables:
  - export/import path preserves traceability and history integrity
  - compatibility across PH-A/PH-C snapshots into PH-D

### 4) Eval Cost and Runtime Control

- IDs: PH-D eval FRs, `TC-P-300`
- Deliverables:
  - explicit eval budget controls
  - no always-on expensive eval path in standard runtime

### 5) Semantic Quality Gates

- IDs: `COV-001`, `FR-005`, `FR-006`, `NO-011`, `ADR-007`, `TC-Q-300`, `TC-Q-301`, `TC-Q-302`
- Deliverables:
  - report semantic quality checks
  - actionability checks for Cursor/Claude usage notes

## Risks and Mitigations

- Plugin escape or direct-write risk -> gate with `TC-I-300`, `TC-S-300`
- Source-boundary regressions -> gate with `TC-I-301`
- Export/import traceability loss -> gate with `TC-E2E-300`
- Eval budget runaway -> gate with `TC-P-300`
- Semantic quality false confidence -> gate with `TC-Q-300`, `TC-Q-301`, `TC-Q-302`

## Checkpoints

1. **CP-D1**: plugin isolation validated (`TC-I-300`, `TC-C-300`, `TC-S-300`).
2. **CP-D2**: source expansion respects mode boundaries (`TC-I-301`).
3. **CP-D3**: export/import compatibility validated (`TC-E2E-300`).
4. **CP-D4**: eval budget/runtime controls validated (`TC-P-300`).
5. **CP-D5**: semantic quality gates green (`TC-Q-300`, `TC-Q-301`, `TC-Q-302`).

## Out-of-Scope List (PH-D)

Still out-of-scope in this lock:

- post-PH-D expansion not represented in approved artifacts
- unplanned product/API expansion not required by PH-D IDs/tests above

## Operational Rules

- test-first remains mandatory (`docs/test-plan.md`, `docs/traceability.md`)
- every implementation PR must reference affected `FR-*`/`NFR-*`/`INV-*`/`SAFE-*` and `TC-*`
- any intentional behavior deviation must be logged as `CR-*` before merge
