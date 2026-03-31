# AIdeator Scope Lock (PH-C)

## Approval Status

- Planning readiness: **GO**
- Lock scope: **PH-C implementation window**
- Lock authority: this file + `docs/execution-plan.md`
- Change policy: any deviation requires explicit `CR-*` entry before implementation

## MVP Features (PH-C Locked In)

PH-A and PH-B baselines are assumed complete; PH-C scope is now:

- multi-user/run isolation (`TC-I-200`)
- backup and restore operations in containerized workflows (`TC-I-201`)
- migration-path reliability (`TC-I-202`)
- compatibility across minor upgrades (`TC-C-200`, `TC-E2E-200`)
- operational hardening:
  - no secret leakage in crash/log output (`TC-S-200`)
  - secure bind defaults (`TC-S-201`)
  - long-run soak stability (`TC-P-200`)

Carry-forward constraints still mandatory:

- `INV-001`..`INV-008`
- `SAFE-001`..`SAFE-003`
- `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`, `NFR-009`, `NFR-010`

## Out-of-Scope Features (Locked Out)

No implementation work for:

- PH-D (`TC-*-300`, `TC-Q-*`): plugin framework, LLM-as-judge quality stack, export/import extensions
- any net-new API/UI surface that is not required by PH-C IDs and tests listed above

## Approved Slice Order (Locked)

1. Isolation foundations (`TC-I-200`)
2. Backup/restore (`TC-I-201`)
3. Migration reliability (`TC-I-202`)
4. Compatibility/upgrade (`TC-C-200`, `TC-E2E-200`)
5. Operational security (`TC-S-200`, `TC-S-201`)
6. Soak/performance (`TC-P-200`)

Do not reorder without updating both lock files.

## Test-First Policy

- Start work from `docs/test-plan.md` and `docs/traceability.md`, not from ad-hoc implementation ideas.
- Every code change must point to affected `TC-*` IDs before merge.
- A PH-C item is not complete until mapped tests are green and traceability still resolves to valid IDs.

Minimum PH-C gates:

- isolation: `TC-I-200`
- durability: `TC-I-201`, `TC-I-202`
- upgrade safety: `TC-C-200`, `TC-E2E-200`
- operational hardening: `TC-S-200`, `TC-S-201`, `TC-P-200`

## Enforcement Rules

- No opportunistic expansion beyond PH-C lock.
- No new ID families; keep `FR-*`, `NFR-*`, `INV-*`, `SAFE-*`, `TC-*`, `ADR-*`, `CR-*`.
- If scope is disputed or unstable, stop implementation and resolve docs first.

## Approval Record

- State: **ACTIVE PH-C LOCK**
- This file is the enforceable boundary for implementation decisions.
