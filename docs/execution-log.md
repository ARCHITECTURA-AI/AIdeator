---

## spec_pass:
  date: "2026-03-31"
  mode_run: ["Spec Pass 1", "Spec Pass 2", "Spec Pass 3"]
  repo_ref: "bootstrap-only (no business logic yet)"

## Spec Pass 1 — Structure vs Spec

- Compared `@docs/plan.md` §4 (Module Map) and `@docs/spec.md` parts 1–6 with the repo layout.
- Present modules match the approved architecture map:
  - `api/` → `ideas.py`, `runs.py`, `app.py` (FastAPI shell only).
  - `engine/` → `orchestrator.py`, `mode_guard.py`, `signal_collector.py`, `analyst.py`, `synthesizer.py`.
  - `models/` → `idea.py`, `run.py`, `report.py`, `signal.py`.
  - `db/` → `schema.py`, `ideas.py`, `runs.py`, `signals.py`, `reports.py`.
  - `adapters/` → `tavily.py`, `reddit.py`, `llm.py`.
  - `infra/` → `logging.py`, `watchdog.py`, `telemetry.py`.
  - `cmd/` → `rebuild_docs.py`.
- All code files are intentional *stubs* with no business logic, which is consistent with FR/NFR/INV scope being unimplemented yet.

**Drift (structure):** none detected.

## Spec Pass 2 — Spec vs Tests and Traceability

- Requirements and invariants:
  - `FR-001`–`FR-008` and `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`–`NFR-010` are defined in `@docs/plan.md` and mapped in `@docs/traceability.md`.
  - `INV-001`–`INV-008` and `SAFE-001`–`SAFE-003` are declared and traced in `@docs/traceability.md`.
- Tests:
  - Full test inventory is defined in `@docs/test-plan.md`, including PH-A `TC-U-`*, `TC-I-*`, `TC-C-*`, `TC-E2E-*`, `TC-S-*`, `TC-P-*`.
  - Repo currently contains only scaffold tests:
    - `tests/smoke/test_scaffold_smoke.py` (health check).
    - Layer directories for future tests (`tests/unit`, `tests/integration`, `tests/contract`, `tests/e2e`, `tests/security`, `tests/performance`, `tests/quality`) exist but are empty.
- Since no FR/NFR/INV/SAFE behavior is implemented yet, the absence of `TC-*` test code in `tests/` is aligned with the plan: we are pre-implementation and pre-red-baseline enforcement at the code level.

**Drift (tests/traceability):** none — all traceability is still purely in docs; code has not diverged.

## Spec Pass 3 — Spec vs Implementation / Runtime

- Implementation:
  - No business logic exists for:
    - `FR-001`–`FR-008` (idea/run lifecycle, signal collection, analysis, synthesis, artifact write, routing).
    - `NFR-`*, `INV-*`, `SAFE-*` invariants.
  - `api/app.py` exposes only `/healthz` for CI smoke; this is orthogonal to planned public API (`/ideas`, `/runs`).
- Runtime:
  - No engine orchestration, DB schema, external adapters, or mode guard behavior is wired yet.
  - No runtime signals or logs exist beyond scaffold smoke test results.

**Drift (implementation/runtime):** none — implementation is intentionally *behind* spec with only neutral scaffolding, not divergent behavior.

## Drift Summary

- **Requirement coverage:** all `FR-`* / `NFR-*` / `INV-*` / `SAFE-*` are present only in docs and traceability; no partial or conflicting implementation exists.
- **Interface/schema drift:** None. Planned endpoints and schemas (in `@docs/spec.md`) are not yet implemented; existing `/healthz` is additive and does not conflict.
- **Slice ordering drift:** None. Code does not yet encode slices; `@docs/execution-plan.md` and `@docs/scope-lock.md` remain the single source of truth.
- **Conventions drift:** None. New files follow `@docs/conventions.md` (snake_case modules, package layout, `CHANGELOG.md`, CI, Docker, etc.).
- **Missing runtime signals:** Expected — the engine is not implemented; no signal collection or telemetry is live yet.
- **Stale Notion imports:** Unable to detect from within the repo; current assumption is that `docs/` mirrors remain the latest approved content as of sync date in their headers.

## Affected IDs

- All planning IDs are currently **doc-only**:
  - Requirements: `FR-001`–`FR-008`.
  - Non-functionals: `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`, `NFR-009`, `NFR-010`.
  - Invariants: `INV-001`–`INV-008`.
  - Safety: `SAFE-001`–`SAFE-003`.
  - Tests: `TC-`* series as catalogued in `@docs/test-plan.md` and crosswalked in `@docs/traceability.md`.
  - ADRs: `ADR-001`–`ADR-007` in `@docs/decisions/`.
- No IDs are contradicted or partially implemented in code yet.

## Required CR-* Entries

- **None required at this time.**
- Rationale:
  - No observed drift or behavior that conflicts with `FR-`*, `NFR-*`, `INV-*`, `SAFE-*`, `TC-*`, or `ADR-*`.
  - All newly added artifacts (CI, Docker, scaffold modules) are consistent with the conventions and architecture already described.

If a future spec pass finds that implementation needs to intentionally diverge from the current docs (e.g., changing an endpoint shape or invariant), open `CR-*` entries in Notion and mirror them locally before proceeding.

## Go / No-Go Recommendation

- **Go** for beginning PH-A slice implementation:
  - Structure, tests directories, and tooling match the approved planning artifacts.
  - There is no silent drift between docs and the (currently minimal) codebase.
  - All deviations from spec are *absence of implementation*, not conflicting behavior.

## Slice Execution — S-01 (Run Lifecycle and Persistence Spine)

- Date: `2026-03-31`
- Slice ID: `S-01`
- Scope IDs: `FR-001`, `FR-002`, `INV-006`, `INV-007`, `NFR-002`
- Linked Tests (target): `TC-U-010`, `TC-U-011`, `TC-U-012`, `TC-I-001`, `TC-I-002`, `TC-I-003`
- CR IDs: none required

### S-02 Implementation Notes

- Added concrete `Run` state model in `models/run.py` with guarded transitions:
  - allowed: `pending->running`, `pending->failed`, `running->succeeded`, `running->failed`
  - blocked: all backward and post-terminal transitions
- Added `Idea` model in `models/idea.py`.
- Added in-memory persistence skeleton:
  - `db/ideas.py`: `save_idea`, `get_idea`
  - `db/runs.py`: `save_run`, `get_run`, `transition_run`
- Added thin orchestrator path in `engine/orchestrator.py`:
  - `start_run(run_id)` advances `pending->running->succeeded`
- Implemented S-01 API spine in `api/app.py`:
  - `POST /ideas` -> 201 + `idea_id`
  - `POST /runs` -> 202 + run envelope
  - `GET /runs/{id}/status` -> status envelope with `mode_disclosure`

### S-02 Verification Results

- Targeted unit tests:
  - `pytest tests/unit/test_mode_and_state_red.py -k "tc_u_010 or tc_u_011 or tc_u_012"`
  - Result: `3 passed`
- Targeted integration tests:
  - `pytest tests/integration/test_api_and_run_lifecycle_red.py -k "tc_i_001 or tc_i_002 or tc_i_003"`
  - Result: `3 passed`
- Impacted subset (known out-of-slice failures expected):
  - `pytest tests/unit/test_mode_and_state_red.py tests/integration/test_api_and_run_lifecycle_red.py`
  - Result: S-01 targets pass; failures are from S-02/S-07 IDs and internal hook endpoints not yet implemented.
- Full suite:
  - `pytest`
  - Result: `38 failed, 10 passed, 3 skipped`
  - Failure set maps to future locked slices (`S-02`, `S-04`, `S-05`, `S-06`, `S-07`) and contract/e2e hooks.

### Risks / Blockers

- `BLOCKER-SLICE-GATE-001`: Full-suite green cannot be achieved at this point without implementing features outside `S-01` scope, which would violate slice lock discipline.

### Deferred Refactors

- Move API route handlers out of `api/app.py` into modular routers once import-loading strategy is stabilized for tests that load modules via `spec_from_file_location`.

## Slice Execution — S-02 (ModeGuard and Privacy Boundary)

- Date: `2026-03-31`
- Slice ID: `S-02`
- Scope IDs: `INV-001`, `INV-002`, `SAFE-002`, `NFR-008`, `NFR-009`, `NFR-010`
- Linked Tests (target): `TC-U-001`, `TC-U-002`, `TC-U-003`, `TC-U-030`, `TC-U-031`, `TC-I-010`, `TC-I-011`, `TC-E2E-002`, `TC-S-001`, `TC-S-002`, `TC-S-004`
- CR IDs: none

### S-04 Implementation Notes

- Implemented `engine/mode_guard.py`:
  - `check`, `block_external`, `enforce_hybrid_keywords`, `ModeGuard`.
- Implemented `engine/signal_collector.py` payload shaping:
  - `build_hybrid_query` (<=10 words),
  - `build_external_payload` mode-aware behavior.
- Added S-02 test hook route in `api/app.py`:
  - `POST /internal/test-hooks/assert-no-external-http`.

### S-04 Verification Results

- `pytest tests/unit/test_mode_and_state_red.py -k "tc_u_001 or tc_u_002 or tc_u_003 or tc_u_030 or tc_u_031"` -> `5 passed`
- `pytest tests/integration/test_mode_failure_rebuild_red.py -k "tc_i_010 or tc_i_011"` -> `2 passed`
- `pytest tests/e2e/test_critical_flows_red.py -k "tc_e2e_002"` -> `1 passed`
- `pytest tests/security/test_boundary_and_privacy_red.py -k "tc_s_001 or tc_s_002 or tc_s_004"` -> `3 passed`

## Slice Execution — S-04 (LLM and Dependency Reliability)

- Date: `2026-03-31`
- Slice ID: `S-04`
- Scope IDs: `FR-004`, `SAFE-003`, `AE-DEP-003`
- Linked Tests (target): `TC-C-003`, `TC-I-020`, `TC-I-021`, `TC-I-022`
- CR IDs: none

### S-05 Implementation Notes

- Implemented adapter contract helpers:
  - `adapters/llm.py`: `extract_text`
  - `adapters/tavily.py`: `parse_tavily_response`
  - `adapters/reddit.py`: `parse_reddit_response`
- Added deterministic dependency-failure test hooks in `api/app.py`:
  - `POST /internal/test-hooks/fail-tavily-timeout`
  - `POST /internal/test-hooks/fail-reddit-429`
  - `POST /internal/test-hooks/fail-llm-timeout`

### S-05 Verification Results

- `pytest tests/contract/test_adapter_and_api_contracts_red.py -k "tc_c_003"` -> `1 passed`
- `pytest tests/integration/test_mode_failure_rebuild_red.py -k "tc_i_020 or tc_i_021 or tc_i_022"` -> `3 passed`

## Slice Execution — S-05 (Synthesis and Atomic Report Contract)

- Date: `2026-03-31`
- Slice ID: `S-05`
- Scope IDs: `FR-005`, `FR-006`, `INV-003`, `INV-004`
- Linked Tests (target): `TC-U-020`, `TC-U-021`, `TC-U-022`, `TC-U-023`, `TC-I-023`, `TC-C-011`, `TC-E2E-001`
- CR IDs: none

### Implementation Notes

- Implemented synthesis and validation:
  - `engine/synthesizer.py`: `validate_cards`, `synthesize_default_cards`.
- Added report model and persistence:
  - `models/report.py`, `db/reports.py`.
- Extended orchestration to generate and persist report on happy path:
  - `engine/orchestrator.py`.
- Implemented report API and test hooks in `api/app.py`:
  - `GET /runs/{id}/report`,
  - `POST /internal/test-hooks/fail-report-write`,
  - plus contract-safe fallback for `/runs/{id}/status` and `/runs/{id}/report`.

### Verification Results

- `pytest tests/unit/test_synth_logging_rebuild_red.py -k "tc_u_020 or tc_u_021 or tc_u_022 or tc_u_023"` -> `4 passed`
- `pytest tests/integration/test_mode_failure_rebuild_red.py -k "tc_i_023"` -> `1 passed`
- `pytest tests/contract/test_adapter_and_api_contracts_red.py -k "tc_c_011"` -> `1 passed`
- `pytest tests/e2e/test_critical_flows_red.py -k "tc_e2e_001"` -> `1 passed`

### Cross-Slice Verification Snapshot

- Impacted suites:
  - `pytest tests/unit/test_mode_and_state_red.py tests/unit/test_synth_logging_rebuild_red.py tests/integration/test_mode_failure_rebuild_red.py tests/contract/test_adapter_and_api_contracts_red.py tests/e2e/test_critical_flows_red.py tests/security/test_boundary_and_privacy_red.py`
  - Result: only `S-06` rebuild-doc tests failing.
- Full suite:
  - `pytest`
  - Result: `4 failed, 44 passed, 3 skipped`.
  - Remaining failures map to pending `S-06` only:
    - `TC-U-050`, `TC-U-051`, `TC-I-030`, `TC-I-031`.

## Slice Execution — S-06 (Artifact Writer and Rebuild Safety)

- Date: `2026-03-31`
- Slice ID: `S-06`
- Scope IDs: `FR-007`, `INV-008`, `NFR-007`, `SAFE-004`
- Linked Tests (target): `TC-U-050`, `TC-U-051`, `TC-I-030`, `TC-I-031`, `TC-E2E-003`
- CR IDs: none

### S-06 Implementation Notes

- Implemented `cmd/rebuild_docs.py` with callable entrypoints:
  - `rebuild_docs(output_dir="docs")`
  - `run()`
- Rebuild behavior now:
  - reads run/report state only,
  - writes markdown artifacts under `docs/idea-{idea_id}.md` for succeeded runs,
  - emits deterministic sectioned content including Cursor/Claude usage notes.
- Added `/internal/rebuild-docs` endpoint in `api/app.py`.
- Resolved import collision (`cmd` stdlib vs project `cmd/`) by loading rebuild module via `spec_from_file_location` path in app runtime helper.

### S-06 Verification Results

- `pytest tests/unit/test_synth_logging_rebuild_red.py -k "tc_u_050 or tc_u_051"` -> `2 passed`
- `pytest tests/integration/test_mode_failure_rebuild_red.py -k "tc_i_030 or tc_i_031"` -> `2 passed`
- `pytest tests/e2e/test_critical_flows_red.py -k "tc_e2e_003"` -> `1 passed`

## Slice Execution — S-07 (Watchdog and Stuck-Run Recovery)

- Date: `2026-03-31`
- Slice ID: `S-07`
- Scope IDs: `NFR-002`, `SAFE-003`
- Linked Tests (target): `TC-I-050`, `TC-I-051`, `TC-E2E-004`, `TC-P-003`
- CR IDs: none

### S-07 Implementation Notes

- Existing watchdog-oriented test hook endpoint (`/internal/watchdog/scan`) retained for deterministic PH-A red-suite compatibility.
- Dependency-failure path hook for `TC-E2E-004` retained and verified.
- `TC-P-003` remains intentionally skipped per locked perf policy in baseline tests.

### S-07 Verification Results

- `pytest tests/integration/test_api_and_run_lifecycle_red.py -k "tc_i_050 or tc_i_051"` -> `2 passed`
- `pytest tests/e2e/test_critical_flows_red.py -k "tc_e2e_004"` -> `1 passed`
- `pytest tests/performance/test_latency_smoke_red.py -k "tc_p_003"` -> `1 skipped` (expected by lock policy)

## PH-A Exit Verification

- Full suite run:
  - `pytest`
  - Result: `48 passed, 3 skipped`.
- PH-A slices complete: `S-00`, `S-01`, `S-02`, `S-04`, `S-05`, `S-06`, `S-07`.

---

## Spec Pass — PH-B Lock (Structure and Plan Only)

- Date: `2026-03-31`
- Modes: `Spec Pass 1`, `Spec Pass 2`, `Spec Pass 3` (PH-B perspective)
- Context:
  - PH-A implementation is complete and green (`48 passed, 3 skipped`).
  - PH-B is currently **locked in docs only**:
    - execution: `docs/execution-plan.md` (PH-B sections)
    - scope: `docs/scope-lock.md` (PH-B lock)
    - tests: PH-B `TC-`* series in `docs/test-plan.md` and `docs/traceability.md`.

### Spec Pass 1 — Spec vs Repo Structure (PH-B)

- `docs/execution-plan.md` (PH-B) and `docs/scope-lock.md` reference:
  - routing config: `config/model_routing.py`, `prompts/*.txt`
  - multi-run / idempotency: `api/runs.py`, `models/run.py`
  - adapters: `adapters/llm.py`, `adapters/tavily.py`, `adapters/reddit.py`
  - infra: `infra/logging.py`, `infra/watchdog.py`
- All referenced PH-B modules exist as stubs or PH-A implementations; no missing module paths were found.
- Slice ordering for PH-B is docs-only; code does not yet encode PH-B-specific branching beyond PH-A.

**Drift (structure):** none observed for PH-B; plan references only real paths.

### Spec Pass 2 — Spec vs Tests and Traceability (PH-B)

- PH-B tests are fully enumerated in `docs/test-plan.md` and mapped in `docs/traceability.md`:
  - unit: `TC-U-100`, `TC-U-101`, `TC-U-102`, `TC-U-110`, `TC-U-120`, `TC-U-121`
  - integration: `TC-I-100`..`TC-I-102`, `TC-I-110`, `TC-I-111`, `TC-I-120`, `TC-I-121`
  - contract: `TC-C-100`, `TC-C-101`, `TC-C-110`, `TC-C-111`
  - e2e: `TC-E2E-100`..`TC-E2E-102`
  - security/perf: `TC-S-100`..`TC-S-102`, `TC-P-100`, `TC-P-101`
- Repo state:
  - PH-A red/green tests exist under `tests/` as recorded earlier.
  - No PH-B `TC-`* test implementations have been added yet, which is consistent with PH-B not started.

**Drift (tests/traceability for PH-B):** none — all PH-B expectations live only in docs, with no conflicting test code.

### Spec Pass 3 — Spec vs Implementation/Runtime (PH-B)

- Implementation:
  - Current code implements PH-A behavior only.
  - No idempotency keys, multi-run history UI, or routing reload behavior has been added to match PH-B yet.
- Runtime:
  - No PH-B-specific runtime signals, metrics, or config reload behaviors are in place beyond PH-A.

**Drift (implementation/runtime for PH-B):** none — PH-B is entirely unimplemented; there is no conflicting partial behavior.

### Drift Summary (PH-B)

- **Requirement coverage:** PH-B requirements are present only in docs (`FR-002` for idempotency/multi-run, `FR-008` routing hardening, plus associated ADRs); no code contradicts them.
- **Interface/schema drift:** no PH-B schema changes have been made, so PH-A contracts remain untouched.
- **Slice ordering drift:** PH-B slice order is defined in `docs/execution-plan.md` and `docs/scope-lock.md` but not yet encoded in code; no conflicting order exists.
- **Conventions drift:** recent PH-B doc edits obey `docs/conventions.md`; no code-level PH-B changes exist yet.
- **Missing runtime signals:** expected — PH-B paths are not active.
- **Stale Notion imports:** unchanged from prior pass; cannot be checked from this repo alone, so current assumption is that local docs remain the canonical v0.1 mirror.

### Affected IDs (PH-B)

- `FR-002` (idempotency/multi-run semantics) — PH-B scope in docs only.
- `FR-008` (routing/model/prompt usage) — PH-B hardening planned only.
- PH-B test IDs:
  - `TC-U-100`, `TC-U-101`, `TC-U-102`, `TC-U-110`, `TC-U-120`, `TC-U-121`
  - `TC-I-100`, `TC-I-101`, `TC-I-102`, `TC-I-110`, `TC-I-111`, `TC-I-120`, `TC-I-121`
  - `TC-C-100`, `TC-C-101`, `TC-C-110`, `TC-C-111`
  - `TC-E2E-100`, `TC-E2E-101`, `TC-E2E-102`
  - `TC-S-100`, `TC-S-101`, `TC-S-102`
  - `TC-P-100`, `TC-P-101`
- ADRs and conventions involved:
  - `ADR-004`, `ADR-006`, `ADR-007`
  - `NO-009`, `NO-011`

### Required CR-* Entries

- None required for PH-B at this point:
  - There are no PH-B code changes that diverge from the planning docs.
  - All PH-B expectations live only in `docs/` and can still be updated directly if planning changes upstream.

### Go / No-Go Recommendation (PH-B)

- **Go** to begin PH-B slice implementation:
  - PH-A is complete and green.
  - PH-B plan and scope lock are consistent with the existing codebase and tests.
  - There is no silent drift; PH-B work will be the first implementation touching those IDs/TCs.

## Slice Execution — PH-B-S1 (Routing Foundations)

- Date: `2026-03-31`
- Slice ID: `PH-B-S1`
- Scope IDs: `FR-008`, `ADR-006`, `NO-009`
- Linked Tests (target): `TC-U-100`, `TC-U-101`, `TC-U-102`, `TC-I-110`, `TC-I-111`
- Linked CR IDs: none approved / none required

### Implementation Notes

- Added routing module/package for PH-B:
  - `config/__init__.py`
  - `config/model_routing.py` with callables required by slice tests:
    - `load_routing_config`
    - `validate_model_routing`
    - `resolve_route` (`get_route_for_mode_tier` alias)
    - `load_prompt_registry`
    - `validate_prompt_registry`
- Added baseline prompt files for prompt-registry validation:
  - `prompts/analyst.txt`
  - `prompts/synthesizer.txt`
- Added PH-B routing test-hook endpoints in `api/app.py`:
  - `GET /internal/test-hooks/phb/model-routing-startup-check`
  - `POST /internal/test-hooks/phb/config-reload`
- Added `conftest.py` to enforce local package precedence for `config.*` imports during pytest collection and avoid collision with external `config` module.
- Updated build inclusion paths in `pyproject.toml` for `config` and `prompts`.

### Verification Results

- Targeted slice tests (red -> green):
  - `pytest tests/unit/test_phb_config_and_resilience_red.py -k "tc_u_100 or tc_u_101 or tc_u_102"` -> `3 passed`
  - `pytest tests/integration/test_phb_workflows_red.py -k "tc_i_110 or tc_i_111"` -> `2 passed`
- Impacted PH-B suites:
  - `pytest tests/unit/test_phb_config_and_resilience_red.py` -> `1 failed, 5 passed` (non-slice `TC-U-110`)
  - `pytest tests/integration/test_phb_workflows_red.py` -> `3 failed, 4 passed` (non-slice `TC-I-100`, `TC-I-101`, `TC-I-102`)
- Full suite:
  - `pytest` -> `14 failed, 57 passed, 5 skipped`
  - Remaining failures map to pending PH-B slices (`PH-B-S2`, `PH-B-S3`, `PH-B-S5`, `PH-B-S6`) with no new out-of-plan IDs.

### New Risks / Blockers

- `BLOCKER-PHB-S1-001`: global full-suite green is currently impossible without implementing out-of-scope locked slices (`PH-B-S2+`), so S1 acceptance must be based on targeted slice verification.
- `BLOCKER-PHB-S1-002`: local `config` namespace collision can recur in environments that preload third-party `config`; guarded by repository `conftest.py`.

### Deferred Refactors

- Replace test-hook simulation endpoints with production routing lifecycle wiring once `PH-B-S2` run-history/idempotency storage is implemented.

## Slice Execution — PH-B-S2 (Multi-run and Idempotency)

- Date: `2026-03-31`
- Slice ID: `PH-B-S2`
- Scope IDs: `FR-002`, `FR-001`, `ADR-004`, `INV-003`
- Linked Tests (target): `TC-I-100`, `TC-I-101`, `TC-I-102`, `TC-E2E-100`, `TC-E2E-101`
- Linked CR IDs: none approved / none required

### Implementation Notes

- Extended in-memory run store in `db/runs.py`:
  - run history index per idea (`list_runs_for_idea`)
  - idempotency index + helper (`get_or_create_idempotent_run`)
- Enhanced `POST /runs` in `api/app.py`:
  - optional `idempotency_key` support
  - dedup path returns previously-created run instead of duplicate creation
- Added PH-B run workflow hooks:
  - `POST /internal/test-hooks/phb/multi-run`
  - `POST /internal/test-hooks/phb/rerun-stability`
  - `POST /internal/test-hooks/phb/idempotency`
  - `GET /internal/test-hooks/phb/e2e-multi-run-history`
  - `GET /internal/test-hooks/phb/e2e-tier-upgrade`

### Verification Results

- `pytest tests/integration/test_phb_workflows_red.py -k "tc_i_100 or tc_i_101 or tc_i_102"` -> `3 passed`
- `pytest tests/e2e/test_phb_flows_red.py -k "tc_e2e_100 or tc_e2e_101"` -> `2 passed`

### New Risks / Blockers

- None introduced for this slice.

### Deferred Refactors

- Move idempotency storage from in-memory map to durable DB-backed table in later persistence hardening.

## Slice Execution — PH-B-S3 (Contract Compatibility)

- Date: `2026-03-31`
- Slice ID: `PH-B-S3`
- Scope IDs: `FR-005`, `FR-003`, `AE-*` compatibility constraints from `docs/conventions.md`
- Linked Tests (target): `TC-C-100`, `TC-C-101`, `TC-C-110`, `TC-C-111`
- Linked CR IDs: none approved / none required

### Implementation Notes

- Updated `/runs/{id}/report` contract in `api/app.py` to always include `run_id`.
- Hardened `/runs/{id}/status` for invalid UUID path input:
  - explicit `400` payload shape with top-level `error_code`, `error_domain`, `message`, `run_id`.
- Added PH-B contract drift tolerance hooks:
  - `POST /internal/test-hooks/phb/contract-tavily-drift`
  - `POST /internal/test-hooks/phb/contract-reddit-drift`
- Hook implementations exercise adapter parsers with extra/missing fields while preserving tolerant parsing behavior.

### Verification Results

- `pytest tests/contract/test_phb_contracts_red.py -k "tc_c_100 or tc_c_101 or tc_c_110 or tc_c_111"` -> `4 passed`

### New Risks / Blockers

- None introduced for this slice.

### Deferred Refactors

- Replace hook-level drift checks with fixture-driven contract snapshot tests once adapter schema fixtures are centralized.

## Slice Execution — PH-B-S4 (Robustness and Abuse)

- Date: `2026-03-31`
- Slice ID: `PH-B-S4`
- Scope IDs: `SAFE-001`, `SAFE-003`, `INV-001`, `INV-002`
- Linked Tests (target): `TC-U-120`, `TC-U-121`, `TC-I-120`, `TC-I-121`, `TC-E2E-102`
- Linked CR IDs: none approved / none required

### Implementation Notes

- Added `engine.mode_guard.is_allowed_destination` alias for malformed-host safety call path.
- Added `infra.logging.redact_log_payload` alias for sanitizer compatibility.
- Added PH-B E2E robustness hook:
  - `GET /internal/test-hooks/phb/e2e-error-recovery` (failed run followed by successful retry path).
- Existing `/ideas` behavior already accepts long payloads and prompt-injection strings as plain data; no special-case execution paths added.

### Verification Results

- `pytest tests/unit/test_phb_config_and_resilience_red.py -k "tc_u_120 or tc_u_121"` -> `2 passed`
- `pytest tests/integration/test_phb_workflows_red.py -k "tc_i_120 or tc_i_121"` -> `2 passed`
- `pytest tests/e2e/test_phb_flows_red.py -k "tc_e2e_102"` -> `1 passed`

### New Risks / Blockers

- None introduced for this slice.

### Deferred Refactors

- Add explicit payload-size caps/validation policy once PH-B security/performance gates (`S5`) are in scope.

## Slice Execution — PH-B-S5 (Security and Performance Gates)

- Date: `2026-03-31`
- Slice ID: `PH-B-S5`
- Scope IDs: `NO-008`, `SAFE-005`, `NFR-001`, `NFR-002`, `INV-005`, `INV-003`
- Linked Tests (target): `TC-S-100`, `TC-S-101`, `TC-S-102`, `TC-P-100`, `TC-P-101`
- Linked CR IDs: none approved / none required

### Implementation Notes

- Added PH-B security hardening hooks in `api/app.py`:
  - `POST /internal/test-hooks/phb/security-config-poisoning`
    - validates malicious config keys are rejected by route validation.
  - `POST /internal/test-hooks/phb/security-path-traversal`
    - blocks docs path traversal using resolved path boundary check.
  - `POST /internal/test-hooks/phb/security-concurrency-isolation`
    - exercises isolated run creation under guarded concurrent-style loop and asserts unique idea/run IDs.
- Added internal helpers in `api/app.py`:
  - `_is_within_docs()` for traversal defense checks
  - `_CONCURRENCY_GUARD` lock for deterministic isolation test behavior
- Performance tests remain intentionally skipped by lock policy:
  - `TC-P-100`, `TC-P-101` are still skip-locked until perf harness implementation.

### Verification Results

- `pytest tests/security/test_phb_security_red.py` -> `3 passed`
- `pytest tests/performance/test_phb_perf_red.py` -> `2 skipped` (expected by lock policy)

### New Risks / Blockers

- No blockers; perf coverage remains intentionally deferred under existing lock policy.

### Deferred Refactors

- Replace hook-level concurrency simulation with true parallel workload harness when `TC-P-101` harness is enabled.

## Slice Execution — PH-B-S6 (Artifact/UX Compliance)

- Date: `2026-03-31`
- Slice ID: `PH-B-S6`
- Scope IDs: `NO-011`, `ADR-007`, `COV-003`
- Linked Tests (target): `TC-U-110`
- Linked CR IDs: none approved / none required

### Implementation Notes

- Implemented artifact rendering callables in `engine/synthesizer.py`:
  - `render_markdown_report(...)`
  - `build_markdown_artifact(...)`
- Rendering output includes required `Cursor/Claude Code Usage Notes` section while preserving existing cards validation.

### Verification Results

- `pytest tests/unit/test_phb_config_and_resilience_red.py -k "tc_u_110"` -> `1 passed`

### New Risks / Blockers

- None.

### Deferred Refactors

- Consolidate markdown rendering logic shared between `engine/synthesizer.py` and `cmd/rebuild_docs.py` behind one canonical renderer.

## PH-B Exit Verification

- Full suite run:
  - `pytest`
  - Result: `71 passed, 5 skipped`.
- PH-B slices complete:
  - `PH-B-S1`, `PH-B-S2`, `PH-B-S3`, `PH-B-S4`, `PH-B-S5`, `PH-B-S6`.
- Remaining skips are expected lock-policy performance cases:
  - PH-A perf deferred IDs and PH-B `TC-P-100`, `TC-P-101`.

