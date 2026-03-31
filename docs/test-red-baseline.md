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
