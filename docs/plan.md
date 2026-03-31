## Purpose
Convert all planning artifacts into a risk-ordered execution plan that Cursor can follow without access to chat history. A developer reading only this page should be able to execute the project from scratch. Local mirrors: `docs/plan.md`, `docs/execution-plan.md`, `docs/scope-lock.md`.
---
## Metadata
<table header-row="true">
<tr>
<td>Field</td>
<td>Value</td>
</tr>
<tr>
<td>Owner</td>
<td>Richard Abishai</td>
</tr>
<tr>
<td>Status</td>
<td>Draft</td>
</tr>
<tr>
<td>Updated At</td>
<td>2026-03-30</td>
</tr>
<tr>
<td>Version</td>
<td>v0.1</td>
</tr>
<tr>
<td>Strategy</td>
<td>Vertical-slice-first (minimal E2E local-only flow before expanding)</td>
</tr>
<tr>
<td>Related</td>
<td>05 Requirements, 06 Engine Core, 07 Spec, 09 Conventions, 10 Properties, 11 Test Plan</td>
</tr>
</table>
---
## 1. Executive Summary
- **What we are building:** AIdeator — a local-first idea validation engine. A user submits a startup idea; the engine collects signals from external sources (or local stubs), analyzes them with an LLM, and produces a structured validation report (4 cards: demand, competition, risk, next steps) plus a deep markdown artifact.
- **Core design constraint:** Three privacy modes — `local-only` (zero outbound), `hybrid` (keyword-only queries), `cloud-enabled` (full context). Mode is set at run creation and is immutable for that run.
- **PH-A delivers:** One vertical slice — idea → local-only run → stubbed signal collection → LLM analysis → cards report → markdown docs. All P0 invariants hold. All PH-A tests pass.
- **PH-B expands:** Model routing config, multi-run per idea, hybrid + cloud-enabled modes, idempotency, prompt registry.
- **PH-C adds:** Multi-user isolation, Docker packaging, backup/restore, migration path.
- **PH-D adds:** Plugin signal sources, quality evals (LLM-as-judge), export/import.
- **Execution strategy:** First slice is the thinnest possible working end-to-end flow in `local-only` mode. All later slices expand from this proven vertical.
- **What must never change casually:** Mode guard logic (INV-001/INV-002), state machine transitions (INV-006), report write atomicity (INV-003), logging privacy (SAFE-001), docs rebuild read-only contract (INV-008).
---
## 2. Engine Summary
### Engine Modes
<table header-row="true">
<tr>
<td>Mode</td>
<td>External HTTP</td>
<td>LLM Location</td>
<td>Query Style</td>
</tr>
<tr>
<td>`local-only`</td>
<td>❌ None</td>
<td>Local (Ollama/stub)</td>
<td>n/a — no external calls</td>
</tr>
<tr>
<td>`hybrid`</td>
<td>✅ Allowed (keyword only)</td>
<td>Local</td>
<td>Keyword string ≤10 words</td>
</tr>
<tr>
<td>`cloud-enabled`</td>
<td>✅ Allowed (full context)</td>
<td>Remote (LiteLLM)</td>
<td>Full description allowed</td>
</tr>
</table>
### Engine Tiers
<table header-row="true">
<tr>
<td>Tier</td>
<td>Model Class</td>
<td>Expected Latency</td>
</tr>
<tr>
<td>`low`</td>
<td>Smallest/fastest local model</td>
<td>Fast</td>
</tr>
<tr>
<td>`medium`</td>
<td>Mid-size local or remote model</td>
<td>Moderate</td>
</tr>
<tr>
<td>`high`</td>
<td>Largest/best remote model</td>
<td>Slower</td>
</tr>
</table>
### Engine Nodes (PH-A)
1. **SignalCollector** — Fetches Tavily (web) + Reddit (community) signals. In `local-only`, returns stub/empty signals. In `hybrid`, uses keyword-only queries. Governed by ModeGuard.
2. **Analyst** — Calls LiteLLM to analyze signals per idea. In `local-only`, calls local Ollama stub.
3. **Synthesizer** — Assembles 4-card JSON report. Validates schema + citation rules. Writes atomically to DB.
4. **DocWriter** — Writes `docs/idea-{id}.md` including Cursor/Claude Code Usage Notes section.
### Key Invariants
<table header-row="true">
<tr>
<td>ID</td>
<td>Rule</td>
</tr>
<tr>
<td>INV-001</td>
<td>`local-only` never makes any external HTTP call</td>
</tr>
<tr>
<td>INV-002</td>
<td>`hybrid` sends keyword-only queries externally, never full description</td>
</tr>
<tr>
<td>INV-003</td>
<td>Report write is all-or-nothing — no partial reports in DB</td>
</tr>
<tr>
<td>INV-004</td>
<td>demand/competition/risk cards must have non-empty citations</td>
</tr>
<tr>
<td>INV-005</td>
<td>No orphan signals — if run fails, signal rows are cleaned up or never committed</td>
</tr>
<tr>
<td>INV-006</td>
<td>Run state machine is append-only; terminal states are final</td>
</tr>
<tr>
<td>INV-007</td>
<td>Run mode is immutable once set</td>
</tr>
<tr>
<td>INV-008</td>
<td>`rebuild-docs` only reads DB and writes to `docs/`; never mutates DB</td>
</tr>
<tr>
<td>SAFE-001</td>
<td>No idea text, titles, or descriptions appear in any log output</td>
</tr>
<tr>
<td>SAFE-002</td>
<td>Trust boundary enforced per mode via ModeGuard before any network call</td>
</tr>
<tr>
<td>SAFE-003</td>
<td>Dependency failures produce clean run failure, never partial success</td>
</tr>
</table>
---
## 3. Requirements and Scope Summary
### PH-A P0 In-Scope
<table header-row="true">
<tr>
<td>ID</td>
<td>Requirement</td>
</tr>
<tr>
<td>FR-001</td>
<td>Create and store ideas</td>
</tr>
<tr>
<td>FR-002</td>
<td>Create and track runs with status, mode, tier</td>
</tr>
<tr>
<td>FR-003</td>
<td>Collect signals (stubbed for local-only; real for hybrid/cloud)</td>
</tr>
<tr>
<td>FR-004</td>
<td>Analyze signals with LLM</td>
</tr>
<tr>
<td>FR-005</td>
<td>Generate 4-card validation report</td>
</tr>
<tr>
<td>FR-006</td>
<td>Enforce citation rules per card type</td>
</tr>
<tr>
<td>FR-007</td>
<td>Persist deep markdown artifact in `docs/`</td>
</tr>
<tr>
<td>FR-008</td>
<td>Use configured model routing (basic config for PH-A)</td>
</tr>
<tr>
<td>NFR-001</td>
<td>Latency bounds by tier/mode (measured and baselined)</td>
</tr>
<tr>
<td>NFR-002</td>
<td>No stuck runs (watchdog fires on stale pending/running)</td>
</tr>
<tr>
<td>NFR-004</td>
<td>Logs never contain idea text or user content</td>
</tr>
<tr>
<td>NFR-007</td>
<td>Docs rebuild is safe and idempotent</td>
</tr>
<tr>
<td>NFR-008–010</td>
<td>Mode semantics enforced by ModeGuard</td>
</tr>
</table>
### Explicitly Out of Scope Until PH-B+
<table header-row="true">
<tr>
<td>What</td>
<td>Reason</td>
</tr>
<tr>
<td>Model routing YAML config</td>
<td>PH-B: hardcode one model in PH-A</td>
</tr>
<tr>
<td>Multiple runs per idea history UI</td>
<td>PH-B</td>
</tr>
<tr>
<td>Idempotency keys on run creation</td>
<td>PH-B</td>
</tr>
<tr>
<td>Hybrid and cloud-enabled full flows</td>
<td>PH-B (ModeGuard structure built in PH-A, other modes stubbed)</td>
</tr>
<tr>
<td>Prompt registry / multiple prompts</td>
<td>PH-B</td>
</tr>
<tr>
<td>Multi-user isolation</td>
<td>PH-C</td>
</tr>
<tr>
<td>Docker packaging and backup/restore</td>
<td>PH-C</td>
</tr>
<tr>
<td>Plugin signal sources</td>
<td>PH-D</td>
</tr>
<tr>
<td>LLM-as-judge quality evals</td>
<td>PH-D</td>
</tr>
<tr>
<td>Any UI beyond raw JSON API responses</td>
<td>Not planned</td>
</tr>
</table>
---
## 4. Architecture Summary
### Module Map
```javascript
api/
  ideas.py          POST /ideas, GET /ideas/{id}
  runs.py           POST /runs, GET /runs/{id}/status, GET /runs/{id}/report

engine/
  orchestrator.py   Top-level run coordinator
  mode_guard.py     Trust boundary enforcement for all outbound calls
  signal_collector.py  Calls Tavily + Reddit (or stubs in local-only)
  analyst.py        LiteLLM call for analysis
  synthesizer.py    Cards JSON assembly + validation + DB write

models/
  idea.py           Idea dataclass/model
  run.py            Run dataclass + state machine
  report.py         Report/cards model + schema validator
  signal.py         Signal row model

db/
  schema.py         SQLite schema migrations
  ideas.py          DB read/write for ideas
  runs.py           DB read/write for runs
  signals.py        DB read/write for signals
  reports.py        DB read/write for reports (atomic)

adapters/
  tavily.py         Tavily HTTP adapter (with ModeGuard check)
  reddit.py         Reddit HTTP adapter (with ModeGuard check)
  llm.py            LiteLLM wrapper

infra/
  logging.py        Structured logging + redaction middleware
  watchdog.py       Stale run scanner + stuck run killer
  telemetry.py      Metrics + spans (basic)

cmd/
  rebuild_docs.py   Regenerate docs/ from DB (read-only)

docs/
  idea-{id}.md      Per-idea deep markdown artifact
  plan.md           Mirror of this handoff
  test-plan.md      Mirror of page 11
  traceability.md   Mirror of traceability matrix
```
### Data Flow (PH-A local-only)
```javascript
POST /ideas
  → ideas.create_idea()
  → DB: ideas row
  → log:idea_created

POST /runs
  → runs.create_run(mode=local-only, tier=low)
  → DB: runs row (status=pending)
  → log:run_created
  → engine.orchestrator.start_run() [async]

orchestrator:
  → mode_guard.check() [local: allow internal only]
  → signal_collector.collect() [local: returns stub signals]
  → analyst.analyze() [local: calls Ollama stub]
  → synthesizer.synthesize() [validates + writes report atomically]
  → doc_writer.write() [writes docs/idea-{id}.md]
  → runs.set_status(succeeded)
  → log:run_status_changed, metric:run_latency_seconds

GET /runs/{id}/report
  → db/reports.get_report()
  → returns cards JSON
```
---
## 5. Risk Register
> **Build strategy locked to:** Minimal end-to-end local-only flow — barebones `/ideas` + `/runs` + a local-only engine stub that returns hardcoded cards, then refine layer by layer.
<table header-row="true">
<tr>
<td>#</td>
<td>Risk</td>
<td>Likelihood</td>
<td>Impact</td>
<td>Mitigation</td>
<td>Slice(s)</td>
</tr>
<tr>
<td>R-001</td>
<td>ModeGuard bypass — external call leaks in local-only mode</td>
<td>Low</td>
<td>Critical</td>
<td>TC-U-002, TC-I-010, TC-E2E-002 all fail red; ModeGuard wraps all HTTP clients</td>
<td>S-02</td>
</tr>
<tr>
<td>R-002</td>
<td>Partial report written to DB on engine failure</td>
<td>Low</td>
<td>High</td>
<td>Atomic transaction in synthesizer; TC-I-023</td>
<td>S-05</td>
</tr>
<tr>
<td>R-003</td>
<td>Run stuck in `pending` or `running` forever</td>
<td>Medium</td>
<td>High</td>
<td>Watchdog on startup; TC-I-050, TC-I-051</td>
<td>S-07</td>
</tr>
<tr>
<td>R-004</td>
<td>Idea text leaks into structured logs</td>
<td>Medium</td>
<td>High</td>
<td>Log redaction middleware; TC-I-040; TC-U-040</td>
<td>S-02</td>
</tr>
<tr>
<td>R-005</td>
<td>Ollama not available in local-only — run fails with no useful error</td>
<td>Medium</td>
<td>Medium</td>
<td>Proper AE-DEP-003 with guidance in error message; TC-I-022</td>
<td>S-04</td>
</tr>
<tr>
<td>R-006</td>
<td>docs/ rebuild corrupts DB state</td>
<td>Low</td>
<td>High</td>
<td>Rebuild-docs is read-only on DB; TC-U-050, TC-I-030</td>
<td>S-06</td>
</tr>
<tr>
<td>R-007</td>
<td>State machine allows backward transitions</td>
<td>Low</td>
<td>High</td>
<td>Explicit guard in `models/run.py`; TC-U-010–012</td>
<td>S-01</td>
</tr>
<tr>
<td>R-008</td>
<td>Hybrid mode sends full description externally</td>
<td>Low</td>
<td>Critical</td>
<td>ModeGuard blocks at payload level; TC-U-003, TC-I-011</td>
<td>S-02 (stubbed in PH-A)</td>
</tr>
<tr>
<td>R-009</td>
<td>Test suite turns green before invariants actually hold</td>
<td>Medium</td>
<td>High</td>
<td>Red baseline enforced in CI before any implementation starts</td>
<td>S-00</td>
</tr>
<tr>
<td>R-010</td>
<td>Scope creep: adding UI, auth, or multi-user prematurely</td>
<td>High</td>
<td>Medium</td>
<td>Scope lock in this document; any addition requires explicit CR-\*</td>
<td>All</td>
</tr>
<tr>
<td>R-011</td>
<td>LiteLLM response shape changes silently</td>
<td>Low</td>
<td>Medium</td>
<td>TC-C-003 — wrapper tests only stable fields</td>
<td>S-04</td>
</tr>
<tr>
<td>R-012</td>
<td>SQLite concurrency issues under parallel runs</td>
<td>Low</td>
<td>Medium</td>
<td>Single-writer design for PH-A; revisit in PH-C</td>
<td>S-01</td>
</tr>
</table>
