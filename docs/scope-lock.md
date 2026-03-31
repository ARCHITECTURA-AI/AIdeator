# AIdeator Scope Lock (PH-B)

## Approval Status

- Planning readiness: **GO**
- Lock scope: **PH-B implementation window**
- Lock authority: this file + `docs/execution-plan.md`
- Change policy: any deviation requires explicit `CR-*` entry before implementation

## MVP Features (PH-B Locked In)

PH-A baseline is assumed complete; PH-B scope is now:

- `FR-002` multi-run behavior and idempotency-key correctness
- `FR-008` model routing and prompt registry hardening (`ADR-006`)
- PH-B contract compatibility (`TC-C-100`..`TC-C-111`)
- PH-B robustness (`TC-U-120`, `TC-U-121`, `TC-I-120`, `TC-I-121`)
- PH-B security/performance gates (`TC-S-100`..`TC-S-102`, `TC-P-100`..`TC-P-101`)
- artifact requirement retention (`TC-U-110`, `NO-011`, `ADR-007`)

Carry-forward constraints still mandatory:

- `INV-001`..`INV-008`
- `SAFE-001`..`SAFE-003`
- `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`, `NFR-009`, `NFR-010`

## Out-of-Scope Features (Locked Out)

No implementation work for:

- PH-C (`TC-*-200`): multi-user/auth isolation, backup/restore automation, migration-path delivery
- PH-D (`TC-*-300`, `TC-Q-*`): plugin framework, LLM-as-judge quality stack, export/import extensions
- any net-new API/UI surface that is not required by PH-B IDs and tests listed above

## Approved Slice Order (Locked)

1. Routing foundations (`TC-U-100`, `TC-U-101`, `TC-U-102`, `TC-I-110`, `TC-I-111`)
2. Multi-run + idempotency (`TC-I-100`, `TC-I-101`, `TC-I-102`, `TC-E2E-100`, `TC-E2E-101`)
3. Contract compatibility (`TC-C-100`, `TC-C-101`, `TC-C-110`, `TC-C-111`)
4. Robustness and abuse (`TC-U-120`, `TC-U-121`, `TC-I-120`, `TC-I-121`, `TC-E2E-102`)
5. Security/performance gates (`TC-S-100`, `TC-S-101`, `TC-S-102`, `TC-P-100`, `TC-P-101`)
6. Artifact compliance (`TC-U-110`)

Do not reorder without updating both lock files.

## Test-First Policy

- Start work from `docs/test-plan.md` and `docs/traceability.md`, not from ad-hoc implementation ideas.
- Every code change must point to affected `TC-*` IDs before merge.
- A PH-B item is not complete until mapped tests are green and traceability still resolves to valid IDs.

Minimum PH-B gates:

- idempotency behavior: `TC-I-102`
- startup/config fail-fast: `TC-I-110`
- backward-compatible response behavior: `TC-C-100`, `TC-C-101`
- security hardening: `TC-S-100`, `TC-S-101`, `TC-S-102`

## Enforcement Rules

- No opportunistic expansion beyond PH-B lock.
- No new ID families; keep `FR-*`, `NFR-*`, `INV-*`, `SAFE-*`, `TC-*`, `ADR-*`, `CR-*`.
- If scope is disputed or unstable, stop implementation and resolve docs first.

## Approval Record

- State: **ACTIVE PH-B LOCK**
- This file is the enforceable boundary for implementation decisions.
