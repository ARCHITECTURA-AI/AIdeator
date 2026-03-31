# Test Changes and Lock Audit

## Change Set (2026-03-31)

### Added Test Files
- `tests/unit/test_mode_and_state_red.py`
- `tests/unit/test_synth_logging_rebuild_red.py`
- `tests/integration/test_api_and_run_lifecycle_red.py`
- `tests/integration/test_mode_failure_rebuild_red.py`
- `tests/contract/test_adapter_and_api_contracts_red.py`
- `tests/e2e/test_critical_flows_red.py`
- `tests/security/test_boundary_and_privacy_red.py`
- `tests/performance/test_latency_smoke_red.py`

### Coverage Intent by Layer
- Unit: mode guard invariants, run state machine invariants, synthesizer validation, log redaction, rebuild-doc safety.
- Integration: idea/run lifecycle, mode semantics, dependency failure handling, stale-run watchdog, rebuild-doc behavior.
- Contract: Tavily/Reddit/LiteLLM adapter shape contracts and API response schema contracts.
- E2E: core idea->run->report flow, local-only no-network assertion, artifact existence, dependency-failure surfacing.
- Security: trust-boundary and privacy invariants.
- Performance: latency/load smoke placeholders explicitly locked as skipped until harness lands.

## Lock Policy (Effective Immediately)
- TC IDs are append-only. Existing IDs in authored tests must not be renumbered.
- Any weakening/removal of tests mapped to `FR-*`, `NFR-*`, `INV-*`, `SAFE-*`, `LIVE-*` requires a change record in this file and matching `docs/traceability.md` edits.
- A test may move between files/layers only if its TC ID and source-ID mapping are preserved.
- `tests/performance/test_latency_smoke_red.py` stays skipped until perf harness is implemented; removing skip requires baseline refresh in `docs/test-red-baseline.md`.
- Red baseline command is pinned to `pytest` until replaced by an approved suite command in CI.

## Red Baseline Run Audit
- Latest run command: `pytest`
- Exit code: `1` (expected)
- Result summary: `47 failed, 1 passed, 3 skipped`
- Evidence file: `docs/test-red-baseline.md`

## Blockers (Not TODOs)
- `BLOCKER-TEST-001`: API contracts cannot pass until `/ideas`, `/runs`, `/runs/{id}/status`, `/runs/{id}/report` routes exist.
- `BLOCKER-TEST-002`: Unit contracts cannot pass until ModeGuard, Run model, SignalCollector, Synthesizer, Logging, and RebuildDocs callables are implemented.
- `BLOCKER-TEST-003`: Integration and security failure-path tests cannot pass until internal test hooks or equivalent deterministic failure injection strategy is implemented.
