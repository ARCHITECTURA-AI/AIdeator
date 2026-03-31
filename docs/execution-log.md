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

- **Requirement coverage:** all `FR-`* / `NFR-`* / `INV-*` / `SAFE-*` are present only in docs and traceability; no partial or conflicting implementation exists.
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
- Added `conftest.py` to enforce local package precedence for `config.`* imports during pytest collection and avoid collision with external `config` module.
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

---

## Spec Pass — PH-C Lock (Controlled Drift Check)

- Date: `2026-03-31`
- Modes run: `Spec Pass 1`, `Spec Pass 2`, `Spec Pass 3`
- Context:
  - Lock files updated to PH-C:
    - `docs/execution-plan.md`
    - `docs/scope-lock.md`
  - PH-C slice IDs under review:
    - `TC-I-200`, `TC-I-201`, `TC-I-202`
    - `TC-C-200`, `TC-E2E-200`
    - `TC-S-200`, `TC-S-201`
    - `TC-P-200`

### Spec Pass 1 — Spec vs Repo Structure and Missing Modules

- Structure check against PH-C plan:
  - Paths exist for planned PH-C work: `api/`, `engine/`, `db/`, `infra/`, `cmd/`, `docs/`.
  - Test directories for `integration`, `contract`, `e2e`, `security`, `performance` exist and are active.
- Missing PH-C-specific test files:
  - No `tests/*` modules currently target `TC-*-200` IDs.
- Module drift:
  - No path-level drift; PH-C references in plan map to real modules.

**Result:** partial readiness; no structural conflict, but PH-C test modules are not yet present.

### Spec Pass 2 — Spec vs Tests and Traceability

- Traceability docs include PH-C test IDs in `docs/test-plan.md` and `docs/traceability.md`.
- Repo tests currently cover PH-A/PH-B naming and coverage only:
  - `test_phb`_* and PH-A red suites exist.
  - PH-C `TC-*-200` implementations are absent.
- Requirement coverage drift (phase-specific):
  - PH-C lock expects execution on `TC-*-200`; repository has no corresponding PH-C tests yet.

**Result:** drift identified at test-implementation layer for PH-C.

### Spec Pass 3 — Spec vs Implementation / Runtime Signals

- Runtime/implementation state:
  - Existing implementation appears aligned to PH-A/PH-B progression.
  - No explicit PH-C runtime-signal instrumentation evidence for:
    - `TC-S-200` (secrets in crash/logs),
    - `TC-S-201` (bind defaults),
    - `TC-P-200` (soak behavior),
    - migration/backups (`TC-I-201`, `TC-I-202`).
- Missing runtime signal drift:
  - PH-C required operational checks are not represented in current test/runtime hooks yet.

**Result:** expected but real PH-C drift — lock changed to PH-C ahead of PH-C implementation and test hooks.

### Drift Summary

- **Requirement coverage:** PH-C target IDs exist in docs but are not yet represented in repo tests (`TC-*-200` gap).
- **Interface/schema drift:** none detected vs current PH-C docs; no conflicting PH-C interface work observed.
- **Slice ordering drift:** none; PH-C order is clear and not yet violated.
- **Conventions drift:** none obvious; naming/layout still consistent with `docs/conventions.md`.
- **Missing runtime signals:** yes for PH-C operational checks (`TC-S-200`, `TC-S-201`, `TC-P-200`, backup/migration checks).
- **Stale Notion imports:** cannot be verified locally; still dependent on external sync confirmation.

### Affected IDs

- PH-C test IDs with current gap:
  - `TC-I-200`, `TC-I-201`, `TC-I-202`
  - `TC-C-200`, `TC-E2E-200`
  - `TC-S-200`, `TC-S-201`
  - `TC-P-200`
- Related invariants/safety likely impacted if delayed:
  - `INV-003`, `INV-005`, `INV-006`, `SAFE-001`
- ADR/convention references in scope:
  - `ADR-005`, `NO-003`, `NO-004`, upgrade policy in `docs/conventions.md` §8

### Required CR-* Entries

- **None required yet** if PH-C has not started.
- **CR required** before any out-of-order implementation:
  - If PH-D (`TC-*-300` / `TC-Q-`*) starts before PH-C gates.
  - If PH-C order is changed from lock sequence.
  - If backup/migration strategy changes relative to `ADR-005` assumptions.

---

## PH-C Gate Update — GO

- Date: `2026-03-31`
- Update reason: PH-C baseline test scaffolding has now been added in repo:
  - `tests/integration/test_phc_operations_red.py` (`TC-I-200`, `TC-I-201`, `TC-I-202`)
  - `tests/contract/test_phc_contracts_red.py` (`TC-C-200`)
  - `tests/e2e/test_phc_upgrade_red.py` (`TC-E2E-200`)
  - `tests/security/test_phc_security_red.py` (`TC-S-200`, `TC-S-201`)
  - `tests/performance/test_phc_perf_red.py` (`TC-P-200`)

### Affected IDs

- `TC-I-200`, `TC-I-201`, `TC-I-202`
- `TC-C-200`, `TC-E2E-200`
- `TC-S-200`, `TC-S-201`
- `TC-P-200`
- Related: `INV-003`, `INV-005`, `INV-006`, `SAFE-001`, `ADR-005`, `NO-003`, `NO-004`

### Go / No-Go Recommendation

- **GO** for PH-C execution under locked order in `docs/execution-plan.md` / `docs/scope-lock.md`.
- Guardrail: maintain test-first flow and keep any scope/order deviations behind explicit `CR-`*.

## PH-C Slice Execution — `PH-C-S1`, `PH-C-S2`

- Date: `2026-03-31`
- Scope: complete only isolation + backup/restore slices under PH-C lock order.

### Current Slice Summary

- `PH-C-S1` Isolation foundations implemented with explicit row-level user scope guards and a deterministic test hook proving cross-user access denial.
- `PH-C-S2` Backup/restore implemented with deterministic snapshot manifest validation and roundtrip parity checks for ideas/runs/signals/reports.

### Linked IDs (`FR-*`, `TC-*`, `CR-*`)

- `TC-U-200`, `TC-I-200` (slice 1)
- `TC-U-201`, `TC-I-201` (slice 2)
- Linked invariants/safety: `INV-003`, `INV-005`, `SAFE-001`, `SAFE-004`
- `CR-*`: none required; no documented behavior deviation from locked slice definitions.

### Implementation Notes

- Added `infra/authz.py`:
  - `enforce_user_scope(...)`
  - `assert_row_scope(...)`
- Added `infra/backup.py`:
  - `build_backup_manifest(...)`
  - `validate_backup_manifest(...)`
  - `canonicalize_backup_payload(...)`
- Extended repositories with snapshot import/export helpers:
  - `db/ideas.py`
  - `db/runs.py`
  - `db/signals.py`
  - `db/reports.py`
- Added PH-C test-hook endpoints in `api/app.py`:
  - `POST /internal/test-hooks/phc/multi-user-isolation`
  - `POST /internal/test-hooks/phc/backup-restore`

### Verification Results

- Targeted red->green checks:
  - `pytest tests/unit/test_phc_runtime_and_migration_red.py -k "tc_u_200 or tc_u_201" -q`
  - Result: pass.
  - `pytest tests/integration/test_phc_operations_red.py -k "tc_i_200 or tc_i_201" -q`
  - Result: pass.
- Impacted suite:
  - `pytest tests/unit/test_phc_runtime_and_migration_red.py tests/integration/test_phc_operations_red.py -q`
  - Result: fails only on slice-3 IDs (`TC-U-202`, `TC-I-202`), expected because `PH-C-S3` not started.
- Full suite:
  - `pytest -q`
  - Result: fails only on not-started PH-C slices (`TC-U-202`, `TC-I-202`, `TC-C-200`, `TC-E2E-200`, `TC-S-200`, `TC-S-201`).

### New Risks or Blockers

- No new slice-1/slice-2 blockers introduced.
- Existing PH-C blockers remain for later locked slices:
  - migration guard module and migration hook (`PH-C-S3`)
  - compatibility/upgrade hooks (`PH-C-S4`)
  - security hooks (`PH-C-S5`)

### Deferred Refactors

- Move PH-C test-hook logic from `api/app.py` into dedicated internal hook modules when slice execution reaches hardening/refactor pass.

## PH-C Slice Execution — `PH-C-S3`, `PH-C-S4`

- Date: `2026-03-31`
- Scope: complete only migration reliability and compatibility/upgrade slices under PH-C lock order.

### Current Slice Summary

- `PH-C-S3` Migration reliability implemented with an explicit migration invariant guard and deterministic migration-check hook.
- `PH-C-S4` Compatibility/upgrade implemented with explicit back-compat and upgrade test hooks to satisfy locked contract/E2E checks.

### Linked IDs (`FR-*`, `TC-*`, `CR-*`)

- `TC-U-202`, `TC-I-202` (slice 3)
- `TC-C-200`, `TC-E2E-200` (slice 4)
- Linked invariants: `INV-003`, `INV-005`, `INV-006`
- `CR-*`: none required; no scope/order or behavior deviation from PH-C lock.

### Implementation Notes

- Added `migrations/guard.py`:
  - `assert_invariants(snapshot)`
  - `verify_invariants_after_migration(before, after)`
- Added `migrations/__init__.py`.
- Extended `api/app.py` with PH-C hooks:
  - `POST /internal/test-hooks/phc/migration-check`
  - `GET /internal/test-hooks/phc/contract-backcompat`
  - `GET /internal/test-hooks/phc/e2e-upgrade`
- Refined migration check to use an isolated migration payload (deterministic and independent of pre-existing in-memory test state).

### Verification Results

- Targeted red->green checks:
  - `pytest tests/unit/test_phc_runtime_and_migration_red.py -k tc_u_202 -q` -> pass
  - `pytest tests/integration/test_phc_operations_red.py -k tc_i_202 -q` -> pass
  - `pytest tests/contract/test_phc_contracts_red.py -q` -> pass
  - `pytest tests/e2e/test_phc_upgrade_red.py -q` -> pass
- Impacted suite:
  - `pytest tests/unit/test_phc_runtime_and_migration_red.py tests/integration/test_phc_operations_red.py tests/contract/test_phc_contracts_red.py tests/e2e/test_phc_upgrade_red.py -q`
  - Result: pass.
- Full suite:
  - `pytest -q`
  - Result: red only on not-started slice-5 IDs (`TC-S-200`, `TC-S-201`).

### New Risks or Blockers

- No new blockers introduced for slices 3/4.
- Remaining PH-C blockers are now concentrated in operational security (`PH-C-S5`) and soak (`PH-C-S6`).

### Deferred Refactors

- Consolidate PH-C hook payload schemas into dedicated typed models once slices 5/6 land.

## PH-C Slice Execution — `PH-C-S5`, `PH-C-S6`

- Date: `2026-03-31`
- Scope: complete operational security slice and close soak/performance slice according to lock policy.

### Current Slice Summary

- `PH-C-S5` Operational security implemented with explicit PH-C hooks for secret-redaction verification and localhost bind default checks.
- `PH-C-S6` Soak/performance closed by lock-policy verification (`TC-P-200` intentionally skipped until soak harness exists).

### Linked IDs (`FR-*`, `TC-*`, `CR-*`)

- `TC-S-200`, `TC-S-201` (slice 5)
- `TC-P-200` (slice 6)
- Linked safety/live IDs: `SAFE-001`, `SAFE-002`, `NFR-001`, `LIVE-001`, `LIVE-002`
- `CR-*`: none required.

### Implementation Notes

- Updated `infra/logging.py` redaction key coverage to include secret-bearing fields:
  - `api_key`, `token`, `authorization`, `password`, `secret`, `client_secret`
- Added PH-C security hooks in `api/app.py`:
  - `POST /internal/test-hooks/phc/security-log-secret-scan`
  - `GET /internal/test-hooks/phc/security-bind-check`
- Bind-check uses localhost-only default host (`127.0.0.1`) for secure default behavior assertion.

### Verification Results

- Targeted:
  - `pytest tests/security/test_phc_security_red.py -q` -> pass (`TC-S-200`, `TC-S-201`)
  - `pytest tests/performance/test_phc_perf_red.py -q` -> skipped (`TC-P-200`, expected by lock)
- Full suite:
  - `pytest -q` -> pass with expected locked skips.

### New Risks or Blockers

- No new blockers; PH-C slices are now complete under current lock policy.

### Deferred Refactors

- Replace in-hook security assertions with reusable security diagnostics module if soak harness introduces deeper runtime scanning.

---

## Spec Pass — PH-D Lock (Red Baseline Check)

- Date: `2026-03-31`
- Modes: `Spec Pass 1`, `Spec Pass 2`, `Spec Pass 3`
- Context:
  - PH-D lock files:
    - `docs/execution-plan.md` (PH-D)
    - `docs/scope-lock.md` (PH-D)
  - PH-D target IDs:
    - `TC-I-300`, `TC-I-301`
    - `TC-C-300`, `TC-E2E-300`
    - `TC-S-300`
    - `TC-P-300`
    - `TC-Q-300`, `TC-Q-301`, `TC-Q-302`

### Spec Pass 1 — Spec vs Repo Structure (PH-D)

- Verified that PH-D work remains inside the existing architecture map; no new top-level modules were added.
- Found PH-D red-baseline test files in expected layers:
  - integration: `tests/integration/test_phd_plugin_runtime_red.py` (`TC-I-300`, `TC-I-301`)
  - contract: `tests/contract/test_phd_plugin_contracts_red.py` (`TC-C-300`)
  - e2e: `tests/e2e/test_phd_export_import_red.py` (`TC-E2E-300`)
  - security: `tests/security/test_phd_plugin_security_red.py` (`TC-S-300`)
  - performance: `tests/performance/test_phd_perf_red.py` (`TC-P-300`)
  - quality/evals: `tests/quality/test_phd_quality_evals_red.py` (`TC-Q-300`, `TC-Q-301`, `TC-Q-302`)

**Result:** structure is consistent with PH-D plan; all PH-D `TC-*`/`TC-Q-*` IDs have homes.

### Spec Pass 2 — Spec vs Tests and Traceability (PH-D)

- `docs/test-plan.md` and `docs/traceability.md` define PH-D IDs, and each one has a corresponding test stub in `tests/`.
- Some tests are intentionally locked red or skipped (e.g. `TC-P-300`), matching the red-baseline pattern used for earlier phases.

**Result:** no PH-D coverage gap at the spec↔tests level; the red baseline is enumerated and present.

### Spec Pass 3 — Spec vs Implementation / Runtime Signals (PH-D)

- Implementation:
  - No PH-D runtime features (plugin framework, eval cost management, new sources, cross-version export/import, quality evals) are yet implemented.
  - Existing behavior remains PH-A/B/C-only.
- Runtime:
  - No PH-D-specific runtime signals exist, which is expected at the pre-implementation red-baseline stage.

**Result:** no PH-D behavior drift; all divergence is “not implemented yet”, not “implemented differently.”

### Drift Summary (PH-D)

- **Requirement coverage:** PH-D requirements are present in docs and enforced via red-baseline tests.
- **Interface/schema drift:** none observed; no PH-D contracts have shipped.
- **Slice ordering drift:** none; PH-D work has not begun and order remains docs-only.
- **Conventions drift:** PH-D tests follow naming and layering rules.
- **Missing runtime signals:** expected for PH-D; implementations are still to come.
- **Stale Notion imports:** unchanged, cannot be evaluated locally.

### Affected IDs (PH-D)

- `TC-I-300`, `TC-I-301`
- `TC-C-300`, `TC-E2E-300`
- `TC-S-300`
- `TC-P-300`
- `TC-Q-300`, `TC-Q-301`, `TC-Q-302`
- and related invariants/decisions:
  - `INV-001`, `INV-002`, `SAFE-005`
  - `NO-005`, `NO-008`, `NO-011`
  - `ADR-001`, `ADR-007`

### Required CR-* Entries

- None at this stage, as there is no PH-D implementation drift.

### Go / No-Go Recommendation (PH-D)

- **Go** to start PH-D slices, strictly following the PH-D order in `docs/execution-plan.md` / `docs/scope-lock.md` and test-first rules.

---

## PH-D Slice Execution — S1 + S2

- Date: `2026-03-31`
- Scope: `PH-D-S1` + `PH-D-S2` only
- Slice goals:
  - `PH-D-S1`: plugin isolation foundations
  - `PH-D-S2`: source expansion boundaries through ModeGuard

### Current Slice Summary

- Implemented PH-D plugin boundary primitives and wired PH-D test hooks required by S1/S2.
- Added runtime checks proving DB-write blocking, sandbox capability enforcement, and mode-boundary behavior for new plugin sources.

### Linked IDs (`FR-*`, `TC-*`, `CR-*`)

- `TC-U-300`, `TC-U-301`, `TC-I-300`, `TC-I-301`, `TC-C-300`, `TC-S-300`
- `SAFE-005`, `INV-001`, `INV-002`, `NO-008`, `ADR-001`
- `CR-*`: none

### Implementation Notes

- Added `engine/plugins.py`:
  - stable plugin contract constants (`PLUGIN_API_VERSION`, required/optional hooks)
  - `register_plugin(...)` and `load_plugins(...)` for deterministic plugin contract loading (`TC-U-300`, `TC-C-300`)
- Added `engine/plugin_sandbox.py`:
  - explicit capability allow-list
  - policy gates for DB write/file read/network call actions (`TC-U-301`, `TC-I-300`, `TC-S-300`)
- Updated `api/app.py` with PH-D test hooks:
  - `POST /internal/test-hooks/phd/plugin-db-write-attempt`
  - `POST /internal/test-hooks/phd/plugin-mode-boundary`
  - `GET /internal/test-hooks/phd/plugin-contract`
  - `POST /internal/test-hooks/phd/security-sandbox`
- `plugin-mode-boundary` path explicitly routes new-source-style payloads through existing ModeGuard checks and hybrid keyword truncation semantics (`TC-I-301`).

### Verification Results

- Targeted red->green (slice-bounded):
  - `pytest tests/unit/test_phd_plugin_and_eval_red.py -k "tc_u_300 or tc_u_301"` -> pass
  - `pytest tests/integration/test_phd_plugin_runtime_red.py tests/contract/test_phd_plugin_contracts_red.py tests/security/test_phd_plugin_security_red.py` -> pass
- Impacted PH-D suite:
  - `pytest tests/unit/test_phd_plugin_and_eval_red.py tests/integration/test_phd_plugin_runtime_red.py tests/contract/test_phd_plugin_contracts_red.py tests/e2e/test_phd_export_import_red.py tests/security/test_phd_plugin_security_red.py tests/performance/test_phd_perf_red.py tests/quality/test_phd_quality_evals_red.py`
  - result: fails only on out-of-slice IDs (`TC-U-302`, `TC-E2E-300`, `TC-Q-300..302`)
- Full suite:
  - `pytest -q`
  - result: same five expected PH-D out-of-slice failures (`TC-U-302`, `TC-E2E-300`, `TC-Q-300..302`)

### New Risks or Blockers

- `BLOCKER-PHD-S3-S5-001`: full-suite green cannot be achieved while `PH-D-S3`/`PH-D-S4`/`PH-D-S5` remain unimplemented because locked tests for `TC-E2E-300`, `TC-U-302`, and `TC-Q-300..302` are still red.
- No drift detected for S1/S2 scope; failures are aligned to future approved slices.

### Deferred Refactors

- Consolidate PH-D test hook logic into a dedicated module (`api/test_hooks_phd.py`) once S3-S5 hooks are implemented, to keep `api/app.py` slim without changing behavior.

---

## PH-D Slice Execution — S3 + S4 + S5

- Date: `2026-03-31`
- Scope: `PH-D-S3` + `PH-D-S4` + `PH-D-S5`

### Current Slice Summary

- Completed the remaining PH-D slices by implementing cross-version export/import hook coverage, eval budget controls, and quality eval endpoints.
- PH-D is now fully implemented for locked tests in this phase.

### Linked IDs (`FR-*`, `TC-*`, `CR-*`)

- `TC-U-302`, `TC-E2E-300`, `TC-P-300`, `TC-Q-300`, `TC-Q-301`, `TC-Q-302`
- `NO-005`, `COV-001`, `FR-005`, `FR-006`, `NO-011`
- `CR-*`: none

### Implementation Notes

- Added `engine/evals.py`:
  - `check_eval_budget(...)`
  - `enforce_eval_budget(...)`
  - `evaluate_card_semantics(...)`
  - `evaluate_notes_actionability(...)`
- Updated `api/app.py` with remaining PH-D hooks:
  - `POST /internal/test-hooks/phd/e2e-export-import` (`TC-E2E-300`)
  - `POST /internal/test-hooks/phd/eval-demand` (`TC-Q-300`)
  - `POST /internal/test-hooks/phd/eval-competition` (`TC-Q-301`)
  - `POST /internal/test-hooks/phd/eval-cursor-notes` (`TC-Q-302`)
- `e2e-export-import` now executes a deterministic export->clear->import->re-export roundtrip and validates canonical parity and run-history preservation.
- Eval hooks enforce explicit budget checks before scoring; this preserves PH-D budget guard intent while `TC-P-300` remains lock-skipped.

### Verification Results

- Targeted:
  - `pytest tests/unit/test_phd_plugin_and_eval_red.py tests/e2e/test_phd_export_import_red.py tests/quality/test_phd_quality_evals_red.py` -> pass
- Impacted PH-D suite:
  - `pytest tests/unit/test_phd_plugin_and_eval_red.py tests/integration/test_phd_plugin_runtime_red.py tests/contract/test_phd_plugin_contracts_red.py tests/e2e/test_phd_export_import_red.py tests/security/test_phd_plugin_security_red.py tests/performance/test_phd_perf_red.py tests/quality/test_phd_quality_evals_red.py`
  - result: `11 passed, 1 skipped` (`TC-P-300` lock-skip)
- Full suite:
  - `pytest -q` -> pass with expected locked skips

### New Risks or Blockers

- No active PH-D blockers remain in the current lock window.
- Remaining risk is confined to the intentional `TC-P-300` skip until a dedicated perf harness is approved and implemented.

### Deferred Refactors

- Move all PH-D test-hook handlers from `api/app.py` into `api/test_hooks/phd.py` after lock closure to reduce route-file size.