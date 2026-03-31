# Test Red Baseline

## Baseline Metadata
- Date: 2026-03-31
- Command: `pytest`
- Workspace: `C:/Users/Richa/OneDrive/Documents/Projects/AIdeator`
- Result: **RED (expected)**, exit code `1`

## Red Evidence Snapshot
- Summary: `47 failed, 1 passed, 3 skipped in 2.29s`
- Passing test: `tests/smoke/test_scaffold_smoke.py::test_healthz_smoke`
- Skipped tests: `TC-P-001`, `TC-P-002`, `TC-P-003` (performance harness intentionally deferred)
- Failure class A (missing endpoints): `/ideas`, `/runs`, `/runs/{id}/status`, `/runs/{id}/report`, `/internal/*` return `404 Not Found`
- Failure class B (missing symbols): `engine.mode_guard`, `models.run`, `engine.signal_collector`, `engine.synthesizer`, `infra.logging`, `adapters.*`, `cmd/rebuild_docs.py` callable contracts not implemented

## Reproducibility
1. From repo root run `pytest`.
2. Confirm non-zero exit code.
3. Confirm failure list includes TC IDs in test names.
4. Confirm failures are deterministic scaffold gaps, not flaky timing assertions.

## Baseline Acceptance Criteria
- Non-zero exit code: satisfied.
- Failure reasons map to known unimplemented modules/routes: satisfied.
- Every authored critical TC ID appears in output: satisfied.
- No random/flaky failure signatures observed: satisfied.

---
## PH-B Baseline Metadata
- Date: 2026-03-31
- Command: `pytest`
- Scope: PH-B `100+` test authoring and lock audit
- Result: **RED (expected)**, exit code `1`

## PH-B Red Evidence Snapshot
- Summary: `19 failed, 52 passed, 5 skipped in 2.22s`
- Newly skipped performance tests: `TC-P-100`, `TC-P-101`
- Failure class A (PH-B hooks/contracts not implemented): missing `/internal/test-hooks/phb/*` endpoints (`404`)
- Failure class B (PH-B config/model-routing not implemented): `config.model_routing` import/symbol gaps
- Failure class C (PH-B contract hardening): response schema mismatches (`TC-C-100`, `TC-C-101`)

## PH-B Reproducibility
1. From repo root run `pytest`.
2. Confirm non-zero exit code.
3. Confirm PH-B failures are concentrated in `TC-*-100+`.
4. Confirm skip list includes `TC-P-100` and `TC-P-101`.

---
## PH-C Baseline Metadata
- Date: 2026-03-31
- Command: `pytest`
- Scope: PH-C `200+` test authoring and lock audit
- Result: **RED (expected)**, exit code `1`

## PH-C Red Evidence Snapshot
- Summary: `10 failed, 71 passed, 6 skipped in 2.17s`
- Newly skipped performance test: `TC-P-200`
- Failure class A (PH-C hooks/contracts not implemented): missing `/internal/test-hooks/phc/*` endpoints (`404`)
- Failure class B (PH-C infra/migration modules missing): `infra.authz`, `infra.backup`, `migrations.guard`

## PH-C Reproducibility
1. From repo root run `pytest`.
2. Confirm non-zero exit code.
3. Confirm PH-C failures are concentrated in `TC-*-200+`.
4. Confirm skip list includes `TC-P-200`.

---
## PH-D Baseline Metadata
- Date: 2026-03-31
- Command: `pytest`
- Scope: PH-D `300+` test authoring and lock audit
- Result: **RED (expected)**, exit code `1`

## PH-D Red Evidence Snapshot
- Summary: `11 failed, 81 passed, 7 skipped in 2.22s`
- Newly skipped performance test: `TC-P-300`
- Failure class A (PH-D hooks/contracts not implemented): missing `/internal/test-hooks/phd/*` endpoints (`404`)
- Failure class B (PH-D plugin/eval modules missing): `engine.plugins`, `engine.plugin_sandbox`, `engine.evals`
- Failure class C (PH-D quality/eval harness missing): `TC-Q-300`, `TC-Q-301`, `TC-Q-302` endpoint hooks absent

## PH-D Reproducibility
1. From repo root run `pytest`.
2. Confirm non-zero exit code.
3. Confirm PH-D failures are concentrated in `TC-*-300+`.
4. Confirm skip list includes `TC-P-300`.
