# AIdeator Execution Plan (PH-B Lock)

## Objective

Turn the mirrored planning docs into a PH-B execution contract that is explicit, test-first, and drift-resistant.

## Project Overview

AIdeator remains a local-first validation engine with three runtime modes:

- `local-only`
- `hybrid`
- `cloud-enabled`

PH-A baseline is treated as complete. This plan locks PH-B expansion only:

- routing and prompt registry hardening (`FR-008`, `ADR-006`)
- multi-run history and idempotency (`FR-002`, `ADR-004`)
- backward-compatible contract growth (`TC-C-100`..`TC-C-111`)
- PH-B security/performance hardening (`TC-S-100`..`TC-S-102`, `TC-P-100`..`TC-P-101`)

## Architecture Summary

PH-B work is constrained to the approved architecture paths:

- API: `api/ideas.py`, `api/runs.py`
- Engine: `engine/orchestrator.py`, `engine/mode_guard.py`, `engine/signal_collector.py`, `engine/analyst.py`, `engine/synthesizer.py`
- DB: `db/schema.py`, `db/runs.py`, `db/reports.py`, `db/signals.py`
- Adapters/config: `adapters/llm.py`, `config/model_routing.py`, `prompts/*.txt`
- Infra: `infra/logging.py`, `infra/watchdog.py`
- Commands/docs: `cmd/rebuild_docs.py`, `docs/`

## Engine Summary (PH-B)

Non-negotiable carry-over properties:

- `INV-001`, `INV-002`: mode boundary still strict
- `INV-003`, `INV-004`: report atomicity/citation integrity still strict
- `INV-007`: run mode immutability still strict
- `SAFE-001`, `SAFE-002`, `SAFE-003`: no privacy/safety regression

PH-B engine additions focus on:

- route/model/prompt validation and reload behavior
- idempotency key behavior on run creation
- multi-run per idea lifecycle correctness

## Build Order (Locked for PH-B)

1. **PH-B Routing Foundations**
   - `TC-U-100`, `TC-U-101`, `TC-U-102`
   - `TC-I-110`, `TC-I-111`
2. **PH-B Multi-run and Idempotency**
   - `TC-I-100`, `TC-I-101`, `TC-I-102`
   - `TC-E2E-100`, `TC-E2E-101`
3. **PH-B Contract Compatibility**
   - `TC-C-100`, `TC-C-101`, `TC-C-110`, `TC-C-111`
4. **PH-B Robustness and Abuse Cases**
   - `TC-U-120`, `TC-U-121`, `TC-I-120`, `TC-I-121`, `TC-E2E-102`
5. **PH-B Security and Performance Gates**
   - `TC-S-100`, `TC-S-101`, `TC-S-102`
   - `TC-P-100`, `TC-P-101`
6. **PH-B Artifact/UX Compliance**
   - `TC-U-110` (Cursor/Claude usage notes section retained in artifacts)

No reordering without updating `docs/scope-lock.md`.

## Slice Status (Local)

- `PH-B-S1` Routing Foundations (`FR-008`, `TC-U-100`, `TC-U-101`, `TC-U-102`, `TC-I-110`, `TC-I-111`): **completed** (`2026-03-31`)
- `PH-B-S2` Multi-run and Idempotency (`FR-002`, `TC-I-100`, `TC-I-101`, `TC-I-102`, `TC-E2E-100`, `TC-E2E-101`): **completed** (`2026-03-31`)
- `PH-B-S3` Contract Compatibility (`TC-C-100`, `TC-C-101`, `TC-C-110`, `TC-C-111`): **completed** (`2026-03-31`)
- `PH-B-S4` Robustness and Abuse (`TC-U-120`, `TC-U-121`, `TC-I-120`, `TC-I-121`, `TC-E2E-102`): **completed** (`2026-03-31`)
- `PH-B-S5` Security and Performance (`TC-S-100`, `TC-S-101`, `TC-S-102`, `TC-P-100`, `TC-P-101`): **completed** (`2026-03-31`)
- `PH-B-S6` Artifact Compliance (`TC-U-110`): **completed** (`2026-03-31`)

## Per-Slice Spec

### 1) Routing Foundations

- IDs: `FR-008`, `ADR-006`, `NO-009`
- Deliverables:
  - strict routing config parse/validation
  - startup fail-fast on bad routing/prompt refs
  - config reload applies to new runs only

### 2) Multi-run and Idempotency

- IDs: `FR-002`, `FR-001`, `ADR-004`, `INV-003`
- Deliverables:
  - multiple runs per idea with clean separation
  - idempotency key prevents duplicate run creation
  - run history remains consistent across retries/failures

### 3) Contract Compatibility

- IDs: `FR-005`, `FR-003`, `AE-*` schema stability from `docs/conventions.md`
- Deliverables:
  - PH-A clients tolerate PH-B optional response fields
  - stable non-2xx error schema (`error_code`, `error_domain`, `message`, `run_id`)
  - tolerant parsers for external adapter minor schema drift

### 4) Robustness and Abuse

- IDs: `SAFE-001`, `SAFE-003`, `INV-001`, `INV-002`
- Deliverables:
  - long-input resilience
  - prompt-injection treated strictly as data
  - hardened mode guard and log sanitizer fuzz safety

### 5) Security and Performance Gates

- IDs: `NO-008`, `SAFE-005`, `NFR-001`, `NFR-002`, `INV-005`, `INV-003`
- Deliverables:
  - config poisoning prevention
  - docs path traversal prevention
  - parallel run isolation under stress
  - latency/throughput regression within PH-B guardrails

### 6) Artifact/UX Compliance

- IDs: `NO-011`, `ADR-007`, `COV-003`
- Deliverables:
  - markdown artifact contains required Cursor/Claude usage notes section

## Risks and Mitigations

- Routing misconfig causes runtime instability -> gate with `TC-U-100`, `TC-U-101`, `TC-I-110`
- Idempotency defects duplicate runs -> gate with `TC-I-102`
- Contract regressions break PH-A clients -> gate with `TC-C-100`, `TC-C-101`
- Security regressions in config/path handling -> gate with `TC-S-100`, `TC-S-101`
- Concurrency cross-contamination -> gate with `TC-S-102`, `TC-P-101`

## Checkpoints

1. **CP-B1**: routing layer stable; no startup/runtime config drift.
2. **CP-B2**: idempotency + multi-run history stable.
3. **CP-B3**: contract compatibility checks all green.
4. **CP-B4**: abuse/security suite all green.
5. **CP-B5 (PH-B Exit)**:
   - `TC-U-100`..`TC-U-121` implemented and green
   - `TC-I-100`..`TC-I-121` implemented and green
   - `TC-C-100`..`TC-C-111` implemented and green
   - `TC-E2E-100`..`TC-E2E-102` implemented and green
   - `TC-S-100`..`TC-S-102` and `TC-P-100`..`TC-P-101` implemented and green

## Out-of-Scope List (PH-B)

Still out-of-scope in this lock:

- PH-C work (`TC-*-200` series): multi-user isolation, backup/restore automation, migration track
- PH-D work (`TC-*-300` and `TC-Q-*`): plugin system and LLM-as-judge eval stack
- Unplanned API/UI expansion not tied to PH-B IDs above

## Operational Rules

- test-first remains mandatory (`docs/test-plan.md`, `docs/traceability.md`)
- every implementation PR must reference affected `FR-*`/`NFR-*`/`INV-*`/`SAFE-*` and `TC-*`
- any intentional behavior deviation must be logged as `CR-*` before merge
