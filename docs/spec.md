## Purpose
Define system behavior in operational terms: flows, trust boundaries, interface contracts, data rules, observability, and recovery logic. This is the source of truth for `docs/spec.md`.
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
<td>Related IDs</td>
<td>05, 06, 08, 10, 11</td>
</tr>
</table>
---
## Part 1: Actors and Trust Boundaries
### Human Actors
<table header-row="true">
<tr>
<td>Actor</td>
<td>Role</td>
<td>Trust Level</td>
</tr>
<tr>
<td>Local User</td>
<td>The single authenticated human running AIdeator on their own machine. Submits ideas, triggers runs, reads reports.</td>
<td>Fully trusted</td>
</tr>
</table>
### System Actors
<table header-row="true">
<tr>
<td>Actor</td>
<td>Role</td>
<td>Trust Level</td>
</tr>
<tr>
<td>FastAPI Layer</td>
<td>HTTP entrypoint; validates payloads; dispatches async tasks.</td>
<td>Internal, trusted</td>
</tr>
<tr>
<td>Engine Orchestrator (LangGraph)</td>
<td>Runs the 3-node validate_idea graph; manages node order and context.</td>
<td>Internal, trusted</td>
</tr>
<tr>
<td>Persistence Layer (Repositories)</td>
<td>Single canonical writer to SQLite for all entity types.</td>
<td>Internal, trusted</td>
</tr>
<tr>
<td>Mode Guard</td>
<td>Enforces data-boundary rules before every outbound call.</td>
<td>Internal, trusted</td>
</tr>
<tr>
<td>Model Router</td>
<td>Resolves (role, tier, mode) to LiteLLM config.</td>
<td>Internal, trusted</td>
</tr>
</table>
### External Dependencies
<table header-row="true">
<tr>
<td>Dependency</td>
<td>Direction</td>
<td>Trust Level</td>
<td>Notes</td>
</tr>
<tr>
<td>Tavily API</td>
<td>Outbound (search queries)</td>
<td>External, untrusted</td>
<td>Blocked in local-only mode. Search terms only in hybrid.</td>
</tr>
<tr>
<td>Reddit API</td>
<td>Outbound (search queries)</td>
<td>External, untrusted</td>
<td>Blocked in local-only mode. Search terms only in hybrid.</td>
</tr>
<tr>
<td>LiteLLM / Cloud LLM</td>
<td>Outbound (prompts)</td>
<td>External, untrusted</td>
<td>Blocked in local-only mode. Idea text may be sent in cloud-enabled.</td>
</tr>
<tr>
<td>Local LLM (Ollama etc.)</td>
<td>Outbound (prompts, local)</td>
<td>External, semi-trusted</td>
<td>Allowed in all modes. Data stays on device.</td>
</tr>
</table>
### Untrusted Data Entry Points
<table header-row="true">
<tr>
<td>Entry Point</td>
<td>Risk</td>
<td>Mitigation</td>
</tr>
<tr>
<td>Idea form inputs (title, description, target user, context)</td>
<td>Prompt injection into LLM calls; stored XSS in Jinja templates.</td>
<td>Sanitise all user inputs before LLM prompt interpolation; escape all template outputs.</td>
</tr>
<tr>
<td>Signal data from Tavily/Reddit</td>
<td>Prompt injection via external content; unreliable/noisy data.</td>
<td>Treat signal snippets as untrusted text; never interpolate raw into system prompts without wrapping.</td>
</tr>
<tr>
<td>YAML config file (model routing)</td>
<td>Misconfiguration; insecure model endpoints.</td>
<td>Validate on startup; fail fast on bad config.</td>
</tr>
</table>
---
## Part 2: Flow Matrix
### Flow 1: Submit New Idea (FR-001)
**Trigger:** User fills and submits New Idea form.
<table header-row="true">
<tr>
<td>Step</td>
<td>Actor</td>
<td>Action</td>
</tr>
<tr>
<td>1</td>
<td>User</td>
<td>POST /ideas with title, description, target_user, context.</td>
</tr>
<tr>
<td>2</td>
<td>FastAPI</td>
<td>Validates payload; checks for required fields.</td>
</tr>
<tr>
<td>3</td>
<td>FastAPI</td>
<td>Writes idea record to SQLite via Ideas repository.</td>
</tr>
<tr>
<td>4</td>
<td>FastAPI</td>
<td>Returns 201 Created with idea_id and idea object.</td>
</tr>
<tr>
<td>5</td>
<td>UI</td>
<td>Redirects to Idea Detail page showing idea metadata and empty runs list.</td>
</tr>
</table>
**Alternate:** Idea with same title already exists.
- Current behaviour (PH-A/B): create as new idea regardless. Deduplication is post-MVP.
**Error:** Missing required field.
- FastAPI returns 422 Unprocessable Entity with field-level error detail.
---
### Flow 2: Start Validation Run (FR-002, FR-003, FR-004, FR-005, FR-006)
**Trigger:** User clicks "Start Validation" on Idea Detail page.
<table header-row="true">
<tr>
<td>Step</td>
<td>Actor</td>
<td>Action</td>
</tr>
<tr>
<td>1</td>
<td>User</td>
<td>POST /runs with idea_id, tier, mode.</td>
</tr>
<tr>
<td>2</td>
<td>FastAPI</td>
<td>Validates payload; verifies idea_id exists.</td>
</tr>
<tr>
<td>3</td>
<td>FastAPI</td>
<td>Writes run record (status = pending) via Runs repository.</td>
</tr>
<tr>
<td>4</td>
<td>FastAPI</td>
<td>Returns 202 Accepted with run_id and polling URL.</td>
</tr>
<tr>
<td>5</td>
<td>UI</td>
<td>Begins polling GET /runs/\{run_id\}/status every 3 seconds.</td>
</tr>
<tr>
<td>6</td>
<td>FastAPI (background)</td>
<td>Dispatches async validate_idea LangGraph task with (idea, tier, mode, run_id).</td>
</tr>
<tr>
<td>7</td>
<td>Orchestrator</td>
<td>Sets run status = running.</td>
</tr>
<tr>
<td>8</td>
<td>SignalCollector (Node 1)</td>
<td>Mode Guard checks; collects signals from Tavily + Reddit; writes signal records.</td>
</tr>
<tr>
<td>9</td>
<td>Analyst (Node 2)</td>
<td>LLM call via LiteLLM; produces structured insights per dimension.</td>
</tr>
<tr>
<td>10</td>
<td>Synthesizer (Node 3)</td>
<td>LLM call via LiteLLM; produces (a) cards JSON, (b) deep markdown report.</td>
</tr>
<tr>
<td>11</td>
<td>Orchestrator</td>
<td>Writes report record; writes docs/idea-\{id\}.md to disk; sets run status = succeeded.</td>
</tr>
<tr>
<td>12</td>
<td>UI (next poll)</td>
<td>Receives status = succeeded; redirects to GET /runs/\{run_id\}/report.</td>
</tr>
</table>
---
### Flow 3: View Report (FR-007)
**Trigger:** User opens a completed run from Idea History.
<table header-row="true">
<tr>
<td>Step</td>
<td>Actor</td>
<td>Action</td>
</tr>
<tr>
<td>1</td>
<td>User</td>
<td>GET /runs/\{run_id\}/report</td>
</tr>
<tr>
<td>2</td>
<td>FastAPI</td>
<td>Loads run + report from DB; loads idea context.</td>
</tr>
<tr>
<td>3</td>
<td>FastAPI</td>
<td>Returns cards JSON + report metadata + mode + data-boundary disclosure.</td>
</tr>
<tr>
<td>4</td>
<td>UI</td>
<td>Renders evidence cards (Demand, Competition, Risk, Next Steps) + mode badge.</td>
</tr>
</table>
---
### Async/Background Flows
**Stale run detection:**
- On app startup and optionally on a scheduled interval, scan for runs with status = running and created_at older than (NFR-001 threshold x 2).
- Mark stale runs as failed with reason = "timed_out_stale".
- Prevents ghost run accumulation (INV-003).
### Idempotency Rules
<table header-row="true">
<tr>
<td>Endpoint</td>
<td>Idempotent?</td>
<td>Notes</td>
</tr>
<tr>
<td>POST /ideas</td>
<td>No</td>
<td>Each POST creates a new idea. Deduplication is post-MVP.</td>
</tr>
<tr>
<td>POST /runs</td>
<td>No (by design)</td>
<td>Each POST creates a new run for the same idea. Supports re-running.</td>
</tr>
<tr>
<td>GET /runs/\{id\}/status</td>
<td>Yes</td>
<td>Read-only; safe to poll repeatedly.</td>
</tr>
<tr>
<td>GET /runs/\{id\}/report</td>
<td>Yes</td>
<td>Read-only; safe to call many times.</td>
</tr>
</table>
---
## Part 3: Error Flow Matrix
<table header-row="true">
<tr>
<td>Trigger</td>
<td>Error Class</td>
<td>System Behaviour</td>
<td>User-Visible Message</td>
</tr>
<tr>
<td>Missing required field in POST /ideas</td>
<td>Input validation</td>
<td>422 with field errors; no DB write.</td>
<td>"Field 'title' is required."</td>
</tr>
<tr>
<td>idea_id not found in POST /runs</td>
<td>Input validation</td>
<td>404; no run created.</td>
<td>"Idea not found. Please create the idea first."</td>
</tr>
<tr>
<td>Tavily API timeout during SignalCollector</td>
<td>Dependency failure</td>
<td>Run marked failed; source error logged.</td>
<td>"Signal collection failed: Tavily did not respond. Please retry."</td>
</tr>
<tr>
<td>Reddit API rate-limit during SignalCollector</td>
<td>Dependency failure</td>
<td>Run marked failed; source error logged.</td>
<td>"Signal collection failed: Reddit API limit reached. Please wait and retry."</td>
</tr>
<tr>
<td>LLM timeout during Analyst or Synthesizer</td>
<td>Resource failure</td>
<td>Run marked failed; timeout logged.</td>
<td>"Analysis timed out. Try the low tier or check your local model."</td>
</tr>
<tr>
<td>Mode Guard blocks outbound call (local-only violation)</td>
<td>Mode violation</td>
<td>Run marked failed; violation recorded.</td>
<td>"Run blocked: a network call was attempted in local-only mode. Check your configuration."</td>
</tr>
<tr>
<td>SQLite write error</td>
<td>Engine-level failure</td>
<td>Run marked failed; error logged.</td>
<td>"Internal error: could not save results. Check disk space or DB integrity."</td>
</tr>
<tr>
<td>Unknown exception in any LangGraph node</td>
<td>Engine-level failure</td>
<td>Run marked failed; exception class + message logged (no traceback exposed).</td>
<td>"Unexpected error during validation. Check logs for run_id \{id\}."</td>
</tr>
</table>
---
## Part 4: Interface Contracts
### POST /ideas
- **Purpose:** Create a new idea record.
- **Request:**
```json
{
  "title": "string, required, max 200 chars",
  "description": "string, required, max 2000 chars",
  "target_user": "string, required, max 500 chars",
  "context": "string, optional, max 1000 chars"
}
```
- **Response 201:**
```json
{
  "idea_id": "uuid",
  "title": "string",
  "created_at": "ISO8601"
}
```
- **Error 422:** Pydantic validation error with per-field detail.
- **Timeout:** N/A (synchronous write, \< 100ms expected).
- **Retry:** Safe to retry on network error; creates a new idea each time.
---
### POST /runs
- **Purpose:** Create a new validation run against an existing idea and dispatch async workflow.
- **Request:**
```json
{
  "idea_id": "uuid, required",
  "tier": "low | medium, required",
  "mode": "local-only | hybrid | cloud-enabled, required"
}
```
- **Response 202:**
```json
{
  "run_id": "uuid",
  "idea_id": "uuid",
  "status": "pending",
  "tier": "low | medium",
  "mode": "local-only | hybrid | cloud-enabled",
  "poll_url": "/runs/{run_id}/status",
  "created_at": "ISO8601"
}
```
- **Error 404:** idea_id not found.
- **Error 422:** Missing or invalid fields.
- **Timeout:** N/A for the HTTP response (returns immediately). Workflow timeout governed by NFR-001.
- **Retry:** Retry on network error creates a new run; previous run continues in background.
---
### GET /runs/\{run_id\}/status
- **Purpose:** Poll for run completion. Used by UI every 3 seconds until terminal state.
- **Response 200:**
```json
{
  "run_id": "uuid",
  "status": "pending | running | succeeded | failed",
  "mode": "local-only | hybrid | cloud-enabled",
  "mode_disclosure": "string (human-readable data boundary description)",
  "started_at": "ISO8601 | null",
  "completed_at": "ISO8601 | null",
  "error_message": "string | null",
  "report_url": "/runs/{run_id}/report | null"
}
```
- **Error 404:** run_id not found.
- **Timeout:** \< 100ms (DB read only).
- **Retry:** Safe; idempotent.
---
### GET /runs/\{run_id\}/report
- **Purpose:** Retrieve the completed validation report (cards + metadata).
- **Response 200:**
```json
{
  "run_id": "uuid",
  "idea_id": "uuid",
  "mode": "local-only | hybrid | cloud-enabled",
  "mode_disclosure": "string",
  "tier": "low | medium",
  "completed_at": "ISO8601",
  "cards": {
    "demand": { "score": "high | medium | low", "summary": "string", "citations": ["url"] },
    "competition": { "score": "high | medium | low", "summary": "string", "citations": ["url"] },
    "risk": { "score": "high | medium | low", "summary": "string", "citations": ["url"] },
    "next_steps": { "items": ["string"] }
  },
  "artifact_path": "docs/idea-{id}.md"
}
```
- **Error 404:** run_id not found or run not yet succeeded.
- **Error 409:** Run exists but status != succeeded (still running or failed).
- **Timeout:** \< 200ms (DB + file path lookup).
- **Retry:** Safe; idempotent.
---
## Part 5: Data Contracts
### Entity: Idea
<table header-row="true">
<tr>
<td>Field</td>
<td>Type</td>
<td>Constraints</td>
<td>Notes</td>
</tr>
<tr>
<td>idea_id</td>
<td>UUID</td>
<td>PK, immutable</td>
<td>Generated on creation.</td>
</tr>
<tr>
<td>title</td>
<td>TEXT</td>
<td>NOT NULL, max 200 chars</td>
<td>User-provided.</td>
</tr>
<tr>
<td>description</td>
<td>TEXT</td>
<td>NOT NULL, max 2000 chars</td>
<td>User-provided.</td>
</tr>
<tr>
<td>target_user</td>
<td>TEXT</td>
<td>NOT NULL, max 500 chars</td>
<td>User-provided.</td>
</tr>
<tr>
<td>context</td>
<td>TEXT</td>
<td>NULL allowed, max 1000 chars</td>
<td>Optional extra context.</td>
</tr>
<tr>
<td>created_at</td>
<td>DATETIME</td>
<td>NOT NULL, set on insert</td>
<td>Immutable after write.</td>
</tr>
</table>
**Lifecycle:** created -\> (many runs) -\> never deleted in MVP.
**Invariant:** idea_id is immutable; title and description are immutable after creation in MVP.
---
### Entity: Run
<table header-row="true">
<tr>
<td>Field</td>
<td>Type</td>
<td>Constraints</td>
<td>Notes</td>
</tr>
<tr>
<td>run_id</td>
<td>UUID</td>
<td>PK, immutable</td>
<td>Generated on creation.</td>
</tr>
<tr>
<td>idea_id</td>
<td>UUID</td>
<td>FK -\> ideas.idea_id, NOT NULL</td>
<td>Run is always linked to an idea.</td>
</tr>
<tr>
<td>tier</td>
<td>TEXT</td>
<td>NOT NULL: low or medium</td>
<td>Immutable after creation.</td>
</tr>
<tr>
<td>mode</td>
<td>TEXT</td>
<td>NOT NULL: local-only, hybrid, cloud-enabled</td>
<td>Immutable after creation.</td>
</tr>
<tr>
<td>status</td>
<td>TEXT</td>
<td>NOT NULL: pending, running, succeeded, failed</td>
<td>Only valid transitions allowed.</td>
</tr>
<tr>
<td>error_message</td>
<td>TEXT</td>
<td>NULL allowed</td>
<td>Populated on failure only.</td>
</tr>
<tr>
<td>created_at</td>
<td>DATETIME</td>
<td>NOT NULL</td>
<td>Immutable.</td>
</tr>
<tr>
<td>started_at</td>
<td>DATETIME</td>
<td>NULL until engine picks up run</td>
<td>Set when status -\> running.</td>
</tr>
<tr>
<td>completed_at</td>
<td>DATETIME</td>
<td>NULL until terminal state</td>
<td>Set when status -\> succeeded or failed.</td>
</tr>
</table>
**Lifecycle transitions:**
- pending -\> running (engine picks up task)
- running -\> succeeded (all nodes complete, report written)
- running -\> failed (any node or dep failure)
- pending -\> failed (stale detection on startup)
**Invariant:** No direct transition from succeeded -\> failed or vice versa. Terminal states are immutable.
---
### Entity: Signal
<table header-row="true">
<tr>
<td>Field</td>
<td>Type</td>
<td>Constraints</td>
<td>Notes</td>
</tr>
<tr>
<td>signal_id</td>
<td>UUID</td>
<td>PK, immutable</td>
<td>Generated on collection.</td>
</tr>
<tr>
<td>run_id</td>
<td>UUID</td>
<td>FK -\> [runs.run](http://runs.run)_id, NOT NULL</td>
<td>Signals belong to a run.</td>
</tr>
<tr>
<td>source</td>
<td>TEXT</td>
<td>NOT NULL: tavily, reddit, x</td>
<td>Source identifier.</td>
</tr>
<tr>
<td>url</td>
<td>TEXT</td>
<td>NOT NULL</td>
<td>Source URL.</td>
</tr>
<tr>
<td>snippet</td>
<td>TEXT</td>
<td>NOT NULL</td>
<td>Raw text snippet from source.</td>
</tr>
<tr>
<td>metadata</td>
<td>JSON</td>
<td>NULL allowed</td>
<td>Source-specific metadata (subreddit, upvotes, etc.).</td>
</tr>
<tr>
<td>collected_at</td>
<td>DATETIME</td>
<td>NOT NULL</td>
<td>Immutable.</td>
</tr>
</table>
**Lifecycle:** written once by SignalCollector; never mutated.
**Invariant:** signal_id is immutable; signals are never updated after write.
---
### Entity: Report
<table header-row="true">
<tr>
<td>Field</td>
<td>Type</td>
<td>Constraints</td>
<td>Notes</td>
</tr>
<tr>
<td>report_id</td>
<td>UUID</td>
<td>PK, immutable</td>
<td>Generated on synthesis.</td>
</tr>
<tr>
<td>run_id</td>
<td>UUID</td>
<td>FK -\> [runs.run](http://runs.run)_id, NOT NULL, UNIQUE</td>
<td>One report per run.</td>
</tr>
<tr>
<td>idea_id</td>
<td>UUID</td>
<td>FK -\> ideas.idea_id, NOT NULL</td>
<td>Denormalised for fast lookup.</td>
</tr>
<tr>
<td>cards_json</td>
<td>JSON</td>
<td>NOT NULL</td>
<td>Short evidence cards: demand, competition, risk, next_steps.</td>
</tr>
<tr>
<td>artifact_path</td>
<td>TEXT</td>
<td>NOT NULL</td>
<td>Relative path to docs/idea-\{id\}.md on disk.</td>
</tr>
<tr>
<td>created_at</td>
<td>DATETIME</td>
<td>NOT NULL</td>
<td>Immutable.</td>
</tr>
</table>
**Lifecycle:** written once by Synthesizer when run completes; never mutated.
**Invariant:** One and only one report per succeeded run. No report written for failed runs.
---
## Part 6: Write Path and Recovery
### Canonical Writers
<table header-row="true">
<tr>
<td>Entity</td>
<td>Canonical Writer</td>
<td>Prohibited Writers</td>
</tr>
<tr>
<td>Idea</td>
<td>FastAPI (POST /ideas handler) via Ideas repository</td>
<td>Direct DB writes from engine nodes or UI</td>
</tr>
<tr>
<td>Run (create + status update)</td>
<td>FastAPI (POST /runs, status updates) + Engine Orchestrator (status transitions only) via Runs repository</td>
<td>No direct SQL from nodes</td>
</tr>
<tr>
<td>Signal</td>
<td>SignalCollector node via Signals repository</td>
<td>All other components</td>
</tr>
<tr>
<td>Report</td>
<td>Synthesizer node via Reports repository + file system writer</td>
<td>All other components</td>
</tr>
<tr>
<td>docs/idea-\{id\}.md</td>
<td>Synthesizer node file writer</td>
<td>All other components</td>
</tr>
</table>
### Prohibited Side-Write Paths
- API layer must never write signal or report records directly.
- LangGraph nodes must never call FastAPI endpoints or write to DB outside of their designated repository.
- UI layer must never modify any entity; it is read-only.
### Rebuild Command Patterns
- `rebuild-docs --run-id {id}`: Regenerate docs/idea-\{id\}.md from the canonical cards_json and signals in SQLite for a given run. Does not re-run the engine.
- `rebuild-docs --all`: Regenerate all missing or outdated docs/ files from DB.
- These commands are CLI utilities; post-MVP could be exposed as API endpoints.
### Consistency Checks
- Every succeeded run must have exactly one report row and one docs/ file.
- Every report row must have a non-empty artifact_path that points to an existing file.
- Every signal row must have a valid run_id FK.
- Stale running runs (older than 2x NFR-001 threshold) are inconsistent state; resolved by startup scan.
---
## Part 7: Observability and Runtime Transparency
### Key Log Events
<table header-row="true">
<tr>
<td>Event</td>
<td>Level</td>
<td>Fields</td>
<td>Notes</td>
</tr>
<tr>
<td>run.created</td>
<td>INFO</td>
<td>run_id, idea_id, tier, mode</td>
<td>On POST /runs</td>
</tr>
<tr>
<td>run.started</td>
<td>INFO</td>
<td>run_id, started_at</td>
<td>When engine picks up task</td>
</tr>
<tr>
<td>node.completed</td>
<td>INFO</td>
<td>run_id, node_name, duration_ms</td>
<td>Per node</td>
</tr>
<tr>
<td>node.failed</td>
<td>ERROR</td>
<td>run_id, node_name, error_class, message</td>
<td>No stack trace in prod; no idea content</td>
</tr>
<tr>
<td>signal.collected</td>
<td>INFO</td>
<td>run_id, source, signal_count</td>
<td>Per source</td>
</tr>
<tr>
<td>run.succeeded</td>
<td>INFO</td>
<td>run_id, total_duration_ms, tier, mode</td>
<td>Terminal</td>
</tr>
<tr>
<td>run.failed</td>
<td>ERROR</td>
<td>run_id, error_class, error_message, tier, mode</td>
<td>Terminal</td>
</tr>
<tr>
<td>mode.violation</td>
<td>WARN</td>
<td>run_id, blocked_call_type, mode</td>
<td>When Mode Guard blocks a call</td>
</tr>
<tr>
<td>[stale.run](http://stale.run).detected</td>
<td>WARN</td>
<td>run_id, created_at, age_seconds</td>
<td>On startup scan</td>
</tr>
</table>
**Rules:**
- No idea text, descriptions, or signal snippet content in any log.
- No API keys or secrets in any log.
- All log events include run_id as a correlation identifier.
### Key Metrics (for future observability layer)
<table header-row="true">
<tr>
<td>Metric</td>
<td>Type</td>
<td>Notes</td>
</tr>
<tr>
<td>run_total</td>
<td>Counter</td>
<td>Total runs created</td>
</tr>
<tr>
<td>run_succeeded_total</td>
<td>Counter</td>
<td>Total succeeded runs</td>
</tr>
<tr>
<td>run_failed_total</td>
<td>Counter</td>
<td>Total failed runs; label by error_class</td>
</tr>
<tr>
<td>run_duration_seconds</td>
<td>Histogram</td>
<td>p50, p90, p99; label by tier</td>
</tr>
<tr>
<td>node_duration_seconds</td>
<td>Histogram</td>
<td>Per node; label by node_name</td>
</tr>
<tr>
<td>signal_count</td>
<td>Histogram</td>
<td>Signals collected per run; label by source</td>
</tr>
<tr>
<td>llm_tokens_used</td>
<td>Counter</td>
<td>Token usage per LLM call; label by role, model</td>
</tr>
</table>
### Correlation IDs
- Each run has a `run_id` (UUID) that serves as the primary correlation ID.
- `run_id` is propagated into all LangGraph node callbacks and log events.
- HTTP responses include `X-Run-ID` header where relevant.
---
## Part 8: Runtime Transparency Rules (NFR-008, NFR-009, NFR-010)
### Mode Definitions and Data-Boundary Disclosures
<table header-row="true">
<tr>
<td>Mode</td>
<td>UI Badge</td>
<td>Data-Boundary Disclosure Text</td>
</tr>
<tr>
<td>local-only</td>
<td>Local Only</td>
<td>All processing stays on this device. No idea text, descriptions, or signals are sent to any external service. Local LLM only.</td>
</tr>
<tr>
<td>hybrid</td>
<td>Hybrid</td>
<td>Search queries (not your idea text) are sent to Tavily and Reddit to find public signals. Your idea text and descriptions stay on this device. LLM runs locally.</td>
</tr>
<tr>
<td>cloud-enabled</td>
<td>Cloud Enabled</td>
<td>Your idea text and signals may be sent to a cloud LLM provider (as configured) and to search APIs (Tavily, Reddit). Review your LiteLLM config to see which provider is active.</td>
</tr>
</table>
### Rules
- Mode badge and disclosure text must appear on every page of the web UI at all times (NFR-008).
- Every API response from GET /runs/\{id\}/status and GET /runs/\{id\}/report must include `mode` and `mode_disclosure` fields (NFR-009).
- If mode = local-only and any node attempts an outbound call with idea content, Mode Guard blocks the call, logs a mode.violation event, and marks the run as failed (NFR-010, INV-001).
- Mode is set at run creation (POST /runs) and is immutable for the lifetime of that run.
---
## Spec Risks and Ambiguities
<table header-row="true">
<tr>
<td>ID</td>
<td>Risk / Ambiguity</td>
<td>Impact</td>
<td>Resolution</td>
</tr>
<tr>
<td>SR-001</td>
<td>Subreddit list for Reddit signal collection not yet defined (AQ-001 from 05).</td>
<td>FR-003 under-specified; affects signal quality.</td>
<td>Define default subreddit list in 09 Conventions before PH-A build.</td>
</tr>
<tr>
<td>SR-002</td>
<td>In hybrid mode, whether search terms can include a short idea summary or only keywords is ambiguous (AQ-002 from 05).</td>
<td>Affects NFR-009 disclosure accuracy.</td>
<td>Decide in 09 Conventions; update mode_disclosure text accordingly.</td>
</tr>
<tr>
<td>SR-003</td>
<td>GET /runs/\{id\}/report returns 404 or 409 when run is not yet succeeded. UI must handle this gracefully without confusing the user.</td>
<td>UX issue if polling and report endpoint are both hit simultaneously.</td>
<td>UI should never call /report until status = succeeded. Enforce in frontend logic.</td>
</tr>
<tr>
<td>SR-004</td>
<td>docs/idea-\{id\}.md file path assumes a writable docs/ directory. Permissions or Docker volume config could break this.</td>
<td>docs/ artifact unavailable.</td>
<td>Define docs/ directory as a required Docker volume mount in PH-C packaging.</td>
</tr>
<tr>
<td>SR-005</td>
<td>Token usage logging (llm_tokens_used metric) requires LiteLLM callback support. Not all providers expose token counts consistently.</td>
<td>Metric may be incomplete for some configurations.</td>
<td>Best-effort in PH-A; document gaps per provider in 09 Conventions.</td>
</tr>
</table>
