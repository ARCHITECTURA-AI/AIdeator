---
sync:
  source: "Notion — 11 Test Plan and Traceability"
  source_url: "https://www.notion.so/33031f134827817a9e04e9d0e0e2650a"
  approved_version: v0.1
  planning_readiness: Go
  synced_at: "2026-03-30"
---

# Traceability Matrix
This file is the **single source of truth** for requirements ↔ tests ↔ implementation ↔ runtime signals. It is a **bi-directional** matrix: every requirement traces forward to at least one test, and every test traces back to at least one requirement.
---
## 1. Conventions
- **Requirement IDs**
	- Functional: `FR-*`
	- Non-functional: `NFR-*`
	- Invariants & properties: `INV-*`, `SAFE-*`, `LIVE-*`
- **Test IDs**
	- Unit: `TC-U-###`
	- Integration: `TC-I-###`
	- Contract: `TC-C-###`
	- End-to-end: `TC-E2E-###`
	- Security: `TC-S-###`
	- Performance: `TC-P-###`
	- Quality/Evals: `TC-Q-###` (PH-D)
- **Implementation Targets**
	- File or module path (e.g., `engine/mode_guard.py`, `api/runs.py`).
- **Runtime Signals**
	- Logs: `log:*`
	- Metrics: `metric:*`
	- Spans: `span:*`
	- Alerts: described in test plan.
Bi-directional traceability is mandatory: no requirement without tests, no test without at least one requirement.
---
## 2. Requirements → Tests (Forward Traceability)
> Own this section as a **table per requirement type**. Add rows as you add/change FR/NFR/INV/SAFE/LIVE.
### 2.1 Functional Requirements (FR-\*)
<table header-row="true">
<tr>
<td>FR ID</td>
<td>Description (short)</td>
<td>Test Case IDs</td>
<td>Implementation Targets</td>
<td>Runtime Signals</td>
</tr>
<tr>
<td>FR-001</td>
<td>Create and store ideas</td>
<td>TC-I-001, TC-E2E-001, TC-I-100</td>
<td>api/ideas.py, db/ideas</td>
<td>log:idea_created</td>
</tr>
<tr>
<td>FR-002</td>
<td>Create and track runs</td>
<td>TC-I-002, TC-I-003, TC-I-050, TC-I-051, TC-E2E-001, TC-E2E-004</td>
<td>api/runs.py, models/run.py, infra/watchdog.py</td>
<td>log:run_created, log:run_status_changed, metric:run_latency_seconds</td>
</tr>
<tr>
<td>FR-003</td>
<td>Collect external signals</td>
<td>TC-I-004, TC-I-010, TC-I-011, TC-C-001, TC-C-002, TC-C-110, TC-C-111</td>
<td>engine/signal_collector.py, adapters/tavily.py, adapters/reddit.py</td>
<td>log:dep_call, log:dep_error, metric:dep_error_total</td>
</tr>
<tr>
<td>FR-004</td>
<td>Analyze and synthesize signals</td>
<td>TC-I-003, TC-I-022, TC-C-003</td>
<td>engine/analyst.py, adapters/llm.py</td>
<td>span:node:Analyst, log:dep_error</td>
</tr>
<tr>
<td>FR-005</td>
<td>Generate cards-based validation summary</td>
<td>TC-U-020, TC-U-021, TC-U-022, TC-U-023, TC-I-003, TC-C-011, TC-E2E-001</td>
<td>engine/synthesizer.py, api/runs.py</td>
<td>log:report_write_attempt, log:report_write_failed, metric:report_write_errors_total</td>
</tr>
<tr>
<td>FR-006</td>
<td>Ensure citations on key cards</td>
<td>TC-U-022, TC-U-023, TC-C-011, TC-E2E-001</td>
<td>engine/synthesizer.py</td>
<td>log:report_write_attempt</td>
</tr>
<tr>
<td>FR-007</td>
<td>Persist deep markdown artifacts</td>
<td>TC-I-001, TC-I-030, TC-I-031, TC-E2E-003</td>
<td>cmd/rebuild_docs.py, db/\*</td>
<td>log:rebuild_docs_completed</td>
</tr>
<tr>
<td>FR-008</td>
<td>Use configured models/prompts</td>
<td>TC-C-003, TC-U-100, TC-U-101, TC-U-102</td>
<td>adapters/llm.py, config/model_routing.py</td>
<td>log:dep_call (LLM)</td>
</tr>
</table>
### 2.2 Non-Functional Requirements (NFR-\*)
<table header-row="true">
<tr>
<td>NFR ID</td>
<td>Description (short)</td>
<td>Test Case IDs</td>
<td>Implementation Targets</td>
<td>Runtime Signals</td>
</tr>
<tr>
<td>NFR-001</td>
<td>Latency bounds by tier and mode</td>
<td>TC-P-001, TC-P-002, TC-P-100, TC-P-101</td>
<td>full pipeline</td>
<td>metric:run_latency_seconds</td>
</tr>
<tr>
<td>NFR-002</td>
<td>Correct state transitions & no stuck runs</td>
<td>TC-U-010, TC-U-011, TC-U-012, TC-I-050, TC-I-051, TC-E2E-004</td>
<td>models/run.py, infra/watchdog.py</td>
<td>log:run_status_changed, metric:run_stuck_count</td>
</tr>
<tr>
<td>NFR-004</td>
<td>Logs safe by default</td>
<td>TC-U-040, TC-U-041, TC-I-040, TC-I-041, TC-U-121</td>
<td>infra/logging.py</td>
<td>log_sanitizer_event, log scans</td>
</tr>
<tr>
<td>NFR-007</td>
<td>Docs rebuild safe and reliable</td>
<td>TC-I-001, TC-I-030, TC-U-050, TC-U-051</td>
<td>cmd/rebuild_docs.py, db/\*</td>
<td>log:rebuild_docs_completed</td>
</tr>
<tr>
<td>NFR-008</td>
<td>Local-only mode semantics</td>
<td>TC-U-001, TC-U-002, TC-I-010, TC-E2E-002</td>
<td>engine/mode_guard.py</td>
<td>metric:mode_violation_total</td>
</tr>
<tr>
<td>NFR-009</td>
<td>Hybrid keyword-only semantics</td>
<td>TC-U-003, TC-U-030, TC-U-031, TC-I-011</td>
<td>engine/mode_guard.py, engine/signal_collector.py</td>
<td>log:mode_guard_decision</td>
</tr>
<tr>
<td>NFR-010</td>
<td>Mode disclosures and safety</td>
<td>TC-U-001–004, TC-I-010–012, TC-E2E-002</td>
<td>mode_guard, HTTP handlers</td>
<td>metric:mode_violation_total</td>
</tr>
</table>
### 2.3 Invariants & Safety (INV-*, SAFE-*, LIVE-\*)
<table header-row="true">
<tr>
<td>ID</td>
<td>Description (short)</td>
<td>Test Case IDs</td>
<td>Implementation Targets</td>
<td>Runtime Signals</td>
</tr>
<tr>
<td>INV-001</td>
<td>Local-only never calls external deps</td>
<td>TC-U-002, TC-I-010, TC-E2E-002, TC-S-001, TC-S-002</td>
<td>engine/mode_guard.py, engine/signal_collector.py</td>
<td>metric:mode_violation_total</td>
</tr>
<tr>
<td>INV-002</td>
<td>Hybrid sends keyword-only external queries</td>
<td>TC-U-003, TC-U-030, TC-U-031, TC-I-011, TC-S-004, TC-I-301</td>
<td>mode_guard, signal_collector</td>
<td>log:mode_guard_decision</td>
</tr>
<tr>
<td>INV-003</td>
<td>Report writes are all-or-nothing</td>
<td>TC-U-020, TC-U-021, TC-I-003, TC-I-023</td>
<td>engine/synthesizer.py, db/reports.py</td>
<td>log:report_write_attempt, metric:report_write_errors_total</td>
</tr>
<tr>
<td>INV-004</td>
<td>Cards structure & citations are enforced</td>
<td>TC-U-022, TC-U-023, TC-E2E-001</td>
<td>engine/synthesizer.py</td>
<td>log:report_write_failed</td>
</tr>
<tr>
<td>INV-005</td>
<td>No orphan signals or reports</td>
<td>TC-I-004, TC-S-102</td>
<td>engine/signal_collector.py, db/signals</td>
<td>log:run_status_changed (failed)</td>
</tr>
<tr>
<td>INV-006</td>
<td>Run state machine is total and safe</td>
<td>TC-U-010, TC-U-011, TC-U-012, TC-I-003</td>
<td>models/run.py, engine/orchestrator.py</td>
<td>log:run_status_changed</td>
</tr>
<tr>
<td>INV-007</td>
<td>Run mode is immutable once set</td>
<td>TC-U-004, TC-I-002</td>
<td>models/run.py, api/runs.py</td>
<td>structural</td>
</tr>
<tr>
<td>INV-008</td>
<td>Rebuild-docs only reads DB and writes docs/</td>
<td>TC-U-050, TC-U-051, TC-I-030, TC-I-031, TC-S-101</td>
<td>cmd/rebuild_docs.py, fs helpers</td>
<td>log:rebuild_docs_completed</td>
</tr>
<tr>
<td>SAFE-001</td>
<td>No idea text or PII in logs</td>
<td>TC-U-040, TC-U-041, TC-I-040, TC-I-041, TC-U-121, TC-S-200</td>
<td>infra/logging.py, infra/runtime</td>
<td>log_sanitizer_event, log scans</td>
</tr>
<tr>
<td>SAFE-002</td>
<td>Trust boundary respected per mode</td>
<td>TC-U-001–003, TC-I-010–011, TC-E2E-002, TC-S-001–002</td>
<td>mode_guard, network clients</td>
<td>metric:mode_violation_total, log:mode_guard_blocked_call</td>
</tr>
<tr>
<td>SAFE-003</td>
<td>Dependency failures fail runs cleanly</td>
<td>TC-I-020–023, TC-E2E-004, TC-E2E-102, TC-S-005</td>
<td>signal/analyst/synth nodes</td>
<td>log:dep_error, metric:dep_error_total</td>
</tr>
<tr>
<td>SAFE-004</td>
<td>Docs rebuild never corrupts primary state</td>
<td>TC-U-050, TC-I-030, TC-I-201</td>
<td>cmd/rebuild_docs.py, backup tooling</td>
<td>log:rebuild_docs_completed, DB snapshot diffs</td>
</tr>
<tr>
<td>SAFE-005</td>
<td>Config and plugins cannot widen trust boundary silently</td>
<td>TC-S-100, TC-S-300, TC-I-300</td>
<td>config loader, plugin sandbox</td>
<td>log:dep_call (no unexpected destinations)</td>
</tr>
<tr>
<td>LIVE-001</td>
<td>No pending runs stuck beyond threshold</td>
<td>TC-I-050, TC-E2E-004</td>
<td>infra/watchdog.py</td>
<td>metric:run_stuck_count</td>
</tr>
<tr>
<td>LIVE-002</td>
<td>No running runs stuck beyond threshold</td>
<td>TC-I-051, TC-P-003</td>
<td>infra/watchdog.py</td>
<td>metric:run_stuck_count, log:run_status_changed</td>
</tr>
<tr>
<td>LIVE-003</td>
<td>Runs make forward progress end-to-end</td>
<td>TC-E2E-001, TC-E2E-002</td>
<td>full pipeline</td>
<td>metric:run_latency_seconds</td>
</tr>
<tr>
<td>LIVE-004</td>
<td>Docs can be fully rebuilt from DB</td>
<td>TC-I-030, TC-I-031, TC-E2E-003</td>
<td>cmd/rebuild_docs.py</td>
<td>log:rebuild_docs_completed</td>
</tr>
</table>
---
## 3. Tests → Requirements (Backward Traceability)
> Use this when you add/modify tests: each new TC-\* row must list its mapped requirements.
<table header-row="true">
<tr>
<td>Test ID</td>
<td>Layer</td>
<td>Purpose (short)</td>
<td>Source IDs</td>
<td>Implementation Targets</td>
</tr>
<tr>
<td>TC-U-001</td>
<td>Unit</td>
<td>ModeGuard allows internal-only in local-only</td>
<td>INV-001, NFR-010</td>
<td>engine/mode_guard.py</td>
</tr>
<tr>
<td>TC-U-002</td>
<td>Unit</td>
<td>ModeGuard blocks external in local-only</td>
<td>INV-001, SAFE-002, NFR-010</td>
<td>engine/mode_guard.py</td>
</tr>
<tr>
<td>TC-U-003</td>
<td>Unit</td>
<td>Hybrid keyword-only enforcement</td>
<td>INV-002, NFR-009</td>
<td>engine/mode_guard.py, engine/signal_collector.py</td>
</tr>
<tr>
<td>TC-U-004</td>
<td>Unit</td>
<td>Mode immutability guard</td>
<td>INV-007</td>
<td>models/run.py</td>
</tr>
<tr>
<td>TC-U-010</td>
<td>Unit</td>
<td>Valid state transitions</td>
<td>INV-006, NFR-002</td>
<td>models/run.py</td>
</tr>
<tr>
<td>TC-U-020</td>
<td>Unit</td>
<td>Cards JSON validation success</td>
<td>INV-003, INV-004, FR-005</td>
<td>engine/synthesizer.py</td>
</tr>
<tr>
<td>TC-U-021</td>
<td>Unit</td>
<td>Missing demand card rejected</td>
<td>INV-003, FR-005</td>
<td>engine/synthesizer.py</td>
</tr>
<tr>
<td>TC-U-022</td>
<td>Unit</td>
<td>Missing citations rejected</td>
<td>INV-004, FR-006</td>
<td>engine/synthesizer.py</td>
</tr>
<tr>
<td>TC-U-023</td>
<td>Unit</td>
<td>next_steps card allowed w/o citations</td>
<td>INV-004, FR-006</td>
<td>engine/synthesizer.py</td>
</tr>
<tr>
<td>TC-U-030</td>
<td>Unit</td>
<td>Reddit query truncation</td>
<td>INV-002, NFR-009</td>
<td>engine/signal_collector.py</td>
</tr>
<tr>
<td>TC-U-040</td>
<td>Unit</td>
<td>Log formatter strips idea text</td>
<td>SAFE-001, NFR-004</td>
<td>infra/logging.py</td>
</tr>
<tr>
<td>TC-U-050</td>
<td>Unit</td>
<td>Rebuild-docs uses only DB reads</td>
<td>SAFE-004, INV-008</td>
<td>cmd/rebuild_docs.py</td>
</tr>
<tr>
<td>TC-I-001</td>
<td>Integration</td>
<td>POST /ideas creates DB row</td>
<td>FR-001, NFR-007</td>
<td>api/ideas.py, db/ideas</td>
</tr>
<tr>
<td>TC-I-002</td>
<td>Integration</td>
<td>POST /runs creates pending run</td>
<td>FR-002, INV-007</td>
<td>api/runs.py, db/runs</td>
</tr>
<tr>
<td>TC-I-003</td>
<td>Integration</td>
<td>Run lifecycle happy path</td>
<td>FR-002–FR-005, INV-003, INV-006</td>
<td>api/runs.py, engine/orchestrator.py</td>
</tr>
<tr>
<td>TC-I-004</td>
<td>Integration</td>
<td>No orphan signals on failure</td>
<td>FR-003, INV-005</td>
<td>engine/signal_collector.py, db/signals</td>
</tr>
<tr>
<td>TC-I-010</td>
<td>Integration</td>
<td>Local-only zero outbound HTTP</td>
<td>INV-001, SAFE-002, NFR-010</td>
<td>mode_guard, signal_collector</td>
</tr>
<tr>
<td>TC-I-011</td>
<td>Integration</td>
<td>Hybrid keyword-only payloads</td>
<td>INV-002, NFR-009</td>
<td>signal_collector</td>
</tr>
<tr>
<td>TC-I-012</td>
<td>Integration</td>
<td>Cloud-enabled richer context</td>
<td>FR-003, FR-004, NFR-010</td>
<td>signal_collector, analyst</td>
</tr>
<tr>
<td>TC-I-020</td>
<td>Integration</td>
<td>Tavily timeout handled as AE-DEP-001</td>
<td>SAFE-003</td>
<td>signal_collector</td>
</tr>
<tr>
<td>TC-I-021</td>
<td>Integration</td>
<td>Reddit 429 handled as AE-DEP-002</td>
<td>SAFE-003</td>
<td></td>
</tr>
<tr>
<td>TC-I-022</td>
<td>Integration</td>
<td>LLM timeout handled as AE-DEP-003</td>
<td>SAFE-003, LIVE-002</td>
<td>analyst</td>
</tr>
<tr>
<td>TC-I-023</td>
<td>Integration</td>
<td>DB write failure handled as AE-ENGINE-002</td>
<td>SAFE-003, INV-003</td>
<td>db/reports.py</td>
</tr>
<tr>
<td>TC-I-030</td>
<td>Integration</td>
<td>Rebuild-docs regenerates all succeeded runs</td>
<td>INV-008, LIVE-004, NFR-007</td>
<td>cmd/rebuild_docs.py</td>
</tr>
<tr>
<td>TC-I-031</td>
<td>Integration</td>
<td>Rebuild-docs skips failed runs</td>
<td>INV-008</td>
<td>cmd/rebuild_docs.py</td>
</tr>
<tr>
<td>TC-I-040</td>
<td>Integration</td>
<td>Logs never contain idea text</td>
<td>SAFE-001</td>
<td>api/\*, infra/logging.py</td>
</tr>
<tr>
<td>TC-I-050</td>
<td>Integration</td>
<td>Stale pending run failed by scanner</td>
<td>LIVE-001, NFR-002</td>
<td>infra/watchdog.py</td>
</tr>
<tr>
<td>TC-I-051</td>
<td>Integration</td>
<td>Stuck running run failed by watchdog</td>
<td>LIVE-002, NFR-002</td>
<td>infra/watchdog.py</td>
</tr>
<tr>
<td>TC-C-001</td>
<td>Contract</td>
<td>Tavily parser tolerant to extra fields</td>
<td>FR-003</td>
<td>adapters/tavily.py</td>
</tr>
<tr>
<td>TC-C-002</td>
<td>Contract</td>
<td>Reddit parser tolerant to missing fields</td>
<td>FR-003</td>
<td>adapters/reddit.py</td>
</tr>
<tr>
<td>TC-C-003</td>
<td>Contract</td>
<td>LiteLLM wrapper shape assumptions</td>
<td>FR-004, FR-008</td>
<td>adapters/llm.py</td>
</tr>
<tr>
<td>TC-E2E-001</td>
<td>E2E</td>
<td>Idea → run → report happy path</td>
<td>FR-001–FR-006, LIVE-003</td>
<td>full stack</td>
</tr>
<tr>
<td>TC-E2E-002</td>
<td>E2E</td>
<td>Local-only full flow, no network</td>
<td>INV-001, SAFE-002, NFR-010, LIVE-003</td>
<td>full stack</td>
</tr>
<tr>
<td>TC-E2E-003</td>
<td>E2E</td>
<td>Deep markdown artifact accessible</td>
<td>FR-007, INV-008, LIVE-004</td>
<td>full stack + docs/</td>
</tr>
<tr>
<td>TC-E2E-004</td>
<td>E2E</td>
<td>Dependency failure surfaced to user</td>
<td>FR-002, SAFE-003, LIVE-001</td>
<td>full stack</td>
</tr>
<tr>
<td>TC-P-001</td>
<td>Perf</td>
<td>Low-tier p95 latency</td>
<td>NFR-001</td>
<td>full stack</td>
</tr>
<tr>
<td>TC-P-002</td>
<td>Perf</td>
<td>Medium-tier p95 latency</td>
<td>NFR-001</td>
<td>full stack</td>
</tr>
<tr>
<td>TC-S-001</td>
<td>Security</td>
<td>ModeGuard block behavior</td>
<td>INV-001, SAFE-002</td>
<td>mode_guard</td>
</tr>
<tr>
<td>TC-S-003</td>
<td>Security</td>
<td>Logs contain no user content</td>
<td>SAFE-001</td>
<td>infra/logging.py</td>
</tr>
</table>
(Extend this as you add PH-B/PH-C/PH-D TC-\* IDs.)
---
## 4. Gaps & Checks
- **Check 1 (forward)**: every `FR-*`, `NFR-*`, `INV-*`, `SAFE-*`, `LIVE-*` appears at least once in section 2.
- **Check 2 (backward)**: every `TC-*` appears at least once in section 3.
- **Check 3 (P0 exit)**:
	- Every P0 requirement has ≥1 test **and** ≥1 runtime signal.
	- No P0 behavior is covered only by E2E; at least one unit/integration test exists.
---
## 5. Maintenance Rules
- When you add a requirement:
	- Add a row in **2.\\**(forward).
	- Add matching rows in **3.** once tests exist.
- When you add a test:
	- Add a row in **3.** and update the relevant row(s) in **2.\\**.
- When you change a log/metric/span name:
	- Update the **Runtime Signals** column for all affected rows.
This file should be reviewed at every **phase gate (PH-A/B/C/D)** to ensure traceability remains complete.

---
## 6. Authored Red-Baseline Test Artifacts (2026-03-31)
- Unit:
  - `tests/unit/test_mode_and_state_red.py`
  - `tests/unit/test_synth_logging_rebuild_red.py`
- Integration:
  - `tests/integration/test_api_and_run_lifecycle_red.py`
  - `tests/integration/test_mode_failure_rebuild_red.py`
- Contract:
  - `tests/contract/test_adapter_and_api_contracts_red.py`
- E2E:
  - `tests/e2e/test_critical_flows_red.py`
- Security:
  - `tests/security/test_boundary_and_privacy_red.py`
- Performance:
  - `tests/performance/test_latency_smoke_red.py`

Execution evidence and lock audit:
- `docs/test-red-baseline.md`
- `docs/test-changes.md`

## 7. PH-B Authored Red-Baseline Artifacts (2026-03-31)
- Unit:
  - `tests/unit/test_phb_config_and_resilience_red.py` (`TC-U-100`, `TC-U-101`, `TC-U-102`, `TC-U-110`, `TC-U-120`, `TC-U-121`)
- Integration:
  - `tests/integration/test_phb_workflows_red.py` (`TC-I-100`, `TC-I-101`, `TC-I-102`, `TC-I-110`, `TC-I-111`, `TC-I-120`, `TC-I-121`)
- Contract:
  - `tests/contract/test_phb_contracts_red.py` (`TC-C-100`, `TC-C-101`, `TC-C-110`, `TC-C-111`)
- E2E:
  - `tests/e2e/test_phb_flows_red.py` (`TC-E2E-100`, `TC-E2E-101`, `TC-E2E-102`)
- Security:
  - `tests/security/test_phb_security_red.py` (`TC-S-100`, `TC-S-101`, `TC-S-102`)
- Performance:
  - `tests/performance/test_phb_perf_red.py` (`TC-P-100`, `TC-P-101`)

Execution evidence and lock audit:
- `docs/test-red-baseline.md` (PH-B section)
- `docs/test-changes.md` (PH-B lock and blockers)

## 8. PH-C Authored Red-Baseline Artifacts (2026-03-31)
- Unit:
  - `tests/unit/test_phc_runtime_and_migration_red.py` (`TC-U-200`, `TC-U-201`, `TC-U-202`)
- Integration:
  - `tests/integration/test_phc_operations_red.py` (`TC-I-200`, `TC-I-201`, `TC-I-202`)
- Contract:
  - `tests/contract/test_phc_contracts_red.py` (`TC-C-200`)
- E2E:
  - `tests/e2e/test_phc_upgrade_red.py` (`TC-E2E-200`)
- Security:
  - `tests/security/test_phc_security_red.py` (`TC-S-200`, `TC-S-201`)
- Performance:
  - `tests/performance/test_phc_perf_red.py` (`TC-P-200`)

Execution evidence and lock audit:
- `docs/test-red-baseline.md` (PH-C section)
- `docs/test-changes.md` (PH-C lock and blockers)
