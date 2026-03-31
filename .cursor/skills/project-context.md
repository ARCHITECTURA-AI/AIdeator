## AIdeator Project Context Skill

Use this skill when:
- deciding slice order or whether a task is in scope
- mapping behavior to requirements and tests
- reasoning about modes, data boundaries, or invariants.

Key docs:
- `@docs/plan.md` – overall plan, risks, and architecture map.
- `@docs/spec.md` – flows, contracts, and trust boundaries.
- `@docs/conventions.md` – naming, migrations, error codes, release policy.
- `@docs/model-routing.md` – prompt/model routing expectations.
- `@docs/test-plan.md` – test inventory and red baseline.
- `@docs/traceability.md` – FR/NFR/INV/SAFE ↔ TC mappings.
- `@docs/execution-plan.md` – slice order and per-slice spec.
- `@docs/scope-lock.md` – MVP scope and out-of-scope features.

When answering:
- quote relevant IDs (e.g. `FR-003`, `INV-001`, `SAFE-001`, `TC-U-020`) and point back to the file.
- keep changes within the locked PH-A scope unless the user explicitly requests a change request.

