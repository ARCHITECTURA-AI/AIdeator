## AIdeator Agents

### Default Agent

- **Role**: General engineering agent for AIdeator.
- **Scope**:
  - Reads and respects local planning docs under `docs/`.
  - Follows `@docs/execution-plan.md` and `@docs/scope-lock.md` for slice order and scope.
  - Enforces test-first and traceability using `@docs/test-plan.md` and `@docs/traceability.md`.
- **Tech stack**: Python 3.10, FastAPI, uvicorn, SQLite.

### Behavior Expectations

- Stay within the locked PH-A scope unless explicitly instructed otherwise.
- Always map work to `FR-*`, `NFR-*`, `INV-*`, `SAFE-*`, `ADR-*`, and `TC-*` where applicable.
- Avoid adding business logic that bypasses `engine/`, `db/`, or `adapters/` structure.
- Prefer small, vertical slices and keep CI (`.github/workflows/ci.yml`) green.

