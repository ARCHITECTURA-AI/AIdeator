# AIdeator Scope Lock (PH-D)

## Approval Status

- Planning readiness: **GO**
- Lock scope: **PH-D implementation window**
- Lock authority: this file + `docs/execution-plan.md`
- Change policy: any deviation requires explicit `CR-*` entry before implementation

## MVP Features (PH-D Locked In)

PH-A, PH-B, and PH-C baselines are assumed complete; PH-D scope is now:

- plugin isolation and extension safety (`TC-I-300`, `TC-C-300`, `TC-S-300`)
- source expansion with mode-safe boundaries (`TC-I-301`)
- export/import compatibility (`TC-E2E-300`)
- eval cost/budget controls (`TC-P-300`)
- semantic quality evaluation gates (`TC-Q-300`, `TC-Q-301`, `TC-Q-302`)

Carry-forward constraints still mandatory:

- `INV-001`..`INV-008`
- `SAFE-001`..`SAFE-003`
- `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`, `NFR-009`, `NFR-010`

## Out-of-Scope Features (Locked Out)

No implementation work for:

- post-PH-D expansion not represented in approved artifacts
- any net-new API/UI surface that is not required by PH-D IDs and tests listed above

## Approved Slice Order (Locked)

1. Plugin isolation foundations (`TC-I-300`, `TC-C-300`, `TC-S-300`)
2. Source expansion boundaries (`TC-I-301`)
3. Export/import compatibility (`TC-E2E-300`)
4. Eval cost/runtime controls (`TC-P-300`)
5. Semantic quality gates (`TC-Q-300`, `TC-Q-301`, `TC-Q-302`)

Do not reorder without updating both lock files.

## Test-First Policy

- Start work from `docs/test-plan.md` and `docs/traceability.md`, not from ad-hoc implementation ideas.
- Every code change must point to affected `TC-*` IDs before merge.
- A PH-D item is not complete until mapped tests are green and traceability still resolves to valid IDs.

Minimum PH-D gates:

- plugin safety: `TC-I-300`, `TC-C-300`, `TC-S-300`
- boundary compliance: `TC-I-301`
- portability/compatibility: `TC-E2E-300`
- runtime cost control: `TC-P-300`
- semantic quality: `TC-Q-300`, `TC-Q-301`, `TC-Q-302`

## Enforcement Rules

- No opportunistic expansion beyond PH-D lock.
- No new ID families; keep `FR-*`, `NFR-*`, `INV-*`, `SAFE-*`, `TC-*`, `ADR-*`, `CR-*`.
- If scope is disputed or unstable, stop implementation and resolve docs first.

## Approval Record

- State: **ACTIVE PH-D LOCK**
- This file is the enforceable boundary for implementation decisions.
