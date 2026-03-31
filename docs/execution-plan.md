# AIdeator Execution Plan

## Objective

Turn planning artifacts into an execution contract that is read-mostly, test-first, and slice-locked.

## Inputs and Source Lock

- Source docs: `docs/plan.md`, `docs/spec.md`, `docs/test-plan.md`, `docs/traceability.md`, `docs/conventions.md`, `docs/model-routing.md`, `docs/NON_OBVIOUS.md`, `docs/decisions/ADR-*.md`
- Handoff source: Notion `12 Cursor Handoff Pack` mirrored in `docs/plan.md`
- ID policy: preserve `FR-*`, `NFR-*`, `INV-*`, `SAFE-*`, `TC-*`, `AE-*`, `ADR-*` exactly

## Project Overview

AIdeator is a local-first idea validation engine. A run produces:

- cards JSON (`demand`, `competition`, `risk`, `next_steps`)
- deep markdown artifact (`docs/idea-{id}.md`)

Core runtime modes:

- `local-only` (no outbound)
- `hybrid` (keyword-only outbound)
- `cloud-enabled` (full context outbound)

Core invariants are non-negotiable: `INV-001` through `INV-008`, `SAFE-001` through `SAFE-003`.

## Architecture Summary

- API: `POST /ideas`, `POST /runs`, `GET /runs/{id}/status`, `GET /runs/{id}/report`
- Engine: `orchestrator`, `mode_guard`, `signal_collector`, `analyst`, `synthesizer`
- Persistence: SQLite repositories (`ideas`, `runs`, `signals`, `reports`)
- Infra: structured logging with redaction, stale-run watchdog, telemetry hooks
- Artifact writer: markdown output in `docs/`

Canonical flow:

1. Create idea (`FR-001`)
2. Create run with mode/tier (`FR-002`)
3. Collect signals (`FR-003`)
4. Analyze with LLM (`FR-004`)
5. Synthesize cards + artifact (`FR-005`, `FR-006`, `FR-007`)
6. Enforce model routing semantics (`FR-008`)

## Engine Summary

- Node 1: SignalCollector (ModeGuard protected)
- Node 2: Analyst
- Node 3: Synthesizer

Must hold:

- `local-only` never performs external HTTP (`INV-001`)
- `hybrid` never sends full idea text externally (`INV-002`)
- report persistence is atomic (`INV-003`)
- citation rules enforced (`INV-004`)
- mode immutable per run (`INV-007`)
- docs rebuild is read-only relative to DB (`INV-008`)

## Build Order (Locked)

Execution uses fixed slice order:

1. `S-00` test harness + red baseline gate
2. `S-01` run state machine + persistence skeleton
3. `S-02` ModeGuard and signal boundary enforcement
4. `S-04` LLM adapter and dependency-failure hardening
5. `S-05` synthesis + atomic report writes + citation validation
6. `S-06` docs writer and rebuild safety
7. `S-07` watchdog and stale-run recovery

Notes:

- `S-03` is intentionally not used in the approved slice map.
- No reordering without explicit scope-lock update.

## Slice Status (Local)

- `S-00`: complete (red baseline established and audited)
- `S-01`: complete
- `S-02`: complete
- `S-04`: complete
- `S-05`: complete
- `S-06`: pending
- `S-07`: pending

## Per-Slice Spec

### S-00: Red Baseline First

- Goal: establish failing test inventory before implementation.
- Required test anchor: red baseline artifact in `docs/test-plan.md` Part 5.
- Checkpoint: no feature code until baseline exists and fails for targeted behaviors.
- Key tests: `TC-E2E-001`, `TC-E2E-002`, representative `TC-U-*`, `TC-I-*`, `TC-C-*`.

### S-01: Run Lifecycle and Persistence Spine

- Scope: run model transitions + repository operations + API shell.
- IDs: `FR-001`, `FR-002`, `INV-006`, `INV-007`, `NFR-002`.
- Must pass:
  - `TC-U-010`, `TC-U-011`, `TC-U-012`
  - `TC-I-001`, `TC-I-002`, `TC-I-003`

### S-02: ModeGuard and Privacy Boundary

- Scope: outbound policy and payload filtering.
- IDs: `INV-001`, `INV-002`, `SAFE-002`, `NFR-008`, `NFR-009`, `NFR-010`.
- Must pass:
  - `TC-U-001`, `TC-U-002`, `TC-U-003`, `TC-U-030`, `TC-U-031`
  - `TC-I-010`, `TC-I-011`, `TC-E2E-002`
  - `TC-S-001`, `TC-S-002`, `TC-S-004`

### S-04: LLM and Dependency Reliability

- Scope: adapter correctness and fail-clean behavior.
- IDs: `FR-004`, `SAFE-003`, `AE-DEP-003`.
- Must pass:
  - `TC-C-003`
  - `TC-I-020`, `TC-I-021`, `TC-I-022`

### S-05: Synthesis and Atomic Report Contract

- Scope: cards schema, citations, atomic DB write.
- IDs: `FR-005`, `FR-006`, `INV-003`, `INV-004`.
- Must pass:
  - `TC-U-020`, `TC-U-021`, `TC-U-022`, `TC-U-023`
  - `TC-I-023`
  - `TC-C-011`, `TC-E2E-001`

### S-06: Artifact Writer and Rebuild Safety

- Scope: markdown artifact emission + rebuild-docs safety model.
- IDs: `FR-007`, `INV-008`, `NFR-007`, `SAFE-004`.
- Must pass:
  - `TC-U-050`, `TC-U-051`
  - `TC-I-030`, `TC-I-031`
  - `TC-E2E-003`

### S-07: Watchdog and Stuck-Run Recovery

- Scope: stale run scanning and terminal failure behavior.
- IDs: `NFR-002`, `SAFE-003`.
- Must pass:
  - `TC-I-050`, `TC-I-051`
  - `TC-E2E-004`
  - `TC-P-003`

## Risks and Mitigations

- `R-001`: local-only leak -> enforce `TC-U-002`, `TC-I-010`, `TC-E2E-002` in S-02
- `R-002`: partial report writes -> atomic transaction + `TC-I-023` in S-05
- `R-003`: stuck runs -> watchdog + `TC-I-050`, `TC-I-051` in S-07
- `R-004`: log leakage -> redaction + `TC-U-040`, `TC-I-040` hard gate
- `R-006`: rebuild mutates DB -> enforce `INV-008` with `TC-U-050`, `TC-I-030`
- `R-009`: false-green progression -> S-00 red-baseline gate before implementation

## Checkpoints (Hard Gates)

1. Gate A (after S-00): baseline exists and is red for targeted behavior classes.
2. Gate B (after S-02): mode boundary and disclosure obligations validated.
3. Gate C (after S-05): synthesis correctness + atomicity proven.
4. Gate D (after S-07): no orphan/stuck run behavior under timeout/stale scenarios.
5. PH-A exit gate: `FR-001` to `FR-008` covered; `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`, `NFR-009`, `NFR-010` covered; and `INV-001` to `INV-008` with `SAFE-001` to `SAFE-003` verified by linked `TC-*`.

## Out-of-Scope List (Enforced)

Deferred until later phases:

- model routing YAML dynamic matrix (`PH-B` harden; PH-A may use basic config only)
- multi-run history UX and idempotency keys (`PH-B`)
- full hybrid/cloud execution as production-complete paths (`PH-B+`)
- multi-user/auth/isolation (`PH-C`)
- Docker packaging and backup/restore automation (`PH-C`)
- plugin signal sources (`PH-D`)
- LLM-as-judge quality evals (`PH-D`)
- any UI-heavy features outside current API-driven scope

## Operational Rules

- test-first is mandatory (red -> green by slice)
- no implementation starts for a slice without explicit test IDs selected
- no new requirement IDs introduced during execution without CR/update to lock docs
