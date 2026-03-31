# AIdeator Scope Lock

## Status
- Approval status: **GO (execution authorized)**
- Lock status: **ACTIVE**
- Change policy: out-of-scope work requires explicit change request before implementation

## MVP Features (Locked In)
The MVP/PH-A execution scope is strictly:
- `FR-001` Create/store ideas
- `FR-002` Create/track runs with mode/tier/status
- `FR-003` Signal collection path (stub-safe for `local-only`)
- `FR-004` LLM analysis
- `FR-005` 4-card report generation
- `FR-006` citation enforcement on demand/competition/risk cards
- `FR-007` markdown artifact persistence in `docs/idea-{id}.md`
- `FR-008` configured model routing usage (PH-A basic profile)

Non-functional and safety scope in MVP:
- `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`, `NFR-009`, `NFR-010`
- `INV-001`..`INV-008`
- `SAFE-001`..`SAFE-003`

## Out-of-Scope Features (Locked Out)
No implementation work for:
- PH-B:
  - full model routing matrix/productization
  - multi-run history UX expansion
  - idempotency keys on run creation
  - prompt registry expansion beyond PH-A baseline
- PH-C:
  - multi-user/auth/isolation
  - Docker packaging + operational backup/restore automation
- PH-D:
  - plugin signal source framework
  - LLM-as-judge quality evaluation stack (`TC-Q-*`)
- Any opportunistic additions not tied to locked IDs above.

## Approved Slice Order (Locked)
1. `S-00`
2. `S-01`
3. `S-02`
4. `S-04`
5. `S-05`
6. `S-06`
7. `S-07`

Constraints:
- Do not reorder slices.
- `S-03` remains unused/reserved in this plan.
- Slice completion requires linked test gate pass.

## Test-First Policy (Non-Negotiable)
- Start each slice by selecting target `TC-*` IDs from `docs/test-plan.md` and `docs/traceability.md`.
- Red baseline must exist before implementation (`Part 5: Red Baseline Artifact`).
- Only transition slice status when:
  - target tests are implemented
  - red-to-green evidence exists for the slice
  - invariant/security tests tied to the slice are green

Minimum gate examples:
- Mode boundary work must include `TC-U-002`, `TC-I-010`, `TC-E2E-002`.
- Atomic report work must include `TC-I-023`.
- Rebuild safety work must include `TC-U-050`, `TC-I-030`.
- Watchdog work must include `TC-I-050`, `TC-I-051`.

## Enforcement Rules
- No new `FR-*`, `NFR-*`, `INV-*`, `SAFE-*` IDs during MVP unless lock is revised.
- No coding on locked-out features, even if "small".
- If a task does not map to locked IDs and approved slice order, it is blocked.
- If scope is disputed, pause implementation and update this lock first.

## Approval Record
- Current state: approved for execution with lock active.
- This file is the local authority for opportunistic feature rejection during implementation.
