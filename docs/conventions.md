## Purpose
Define the boring-but-critical rules that make AIdeator maintainable, reproducible, and supportable before code starts. Every convention here is auditable, not aspirational. No exceptions without a Change Request.
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
<td>08, 12</td>
</tr>
</table>
---
## 1. Naming Conventions
<table header-row="true">
<tr>
<td>Entity</td>
<td>Pattern</td>
<td>Example</td>
</tr>
<tr>
<td>Python variables and functions</td>
<td>snake_case</td>
<td>`run_id`, `collect_signals()`</td>
</tr>
<tr>
<td>Python classes</td>
<td>PascalCase</td>
<td>`SignalCollector`, `ModelRouter`</td>
</tr>
<tr>
<td>Python files</td>
<td>snake_case</td>
<td>`signal_collector.py`, `model_router.py`</td>
</tr>
<tr>
<td>Jinja templates</td>
<td>snake_case</td>
<td>`idea_detail.html`, `new_validation.html`</td>
</tr>
<tr>
<td>Environment variables</td>
<td>UPPER_SNAKE_CASE</td>
<td>`TAVILY_API_KEY`, `REDDIT_CLIENT_ID`</td>
</tr>
<tr>
<td>Database tables</td>
<td>snake_case, plural</td>
<td>`ideas`, `runs`, `signals`, `reports`</td>
</tr>
<tr>
<td>Prompt files</td>
<td>\{role\}_v\{major\}.\{minor\}.\{patch\}.txt</td>
<td>`analysis_v1.0.0.txt`, `synthesis_v1.0.0.txt`</td>
</tr>
<tr>
<td>Migration files</td>
<td>\{NNNN\}_\{description\}.sql</td>
<td>`0001_init.sql`, `0002_add_reports.sql`</td>
</tr>
<tr>
<td>Docker volumes</td>
<td>aideator_\{purpose\}</td>
<td>`aideator_db`, `aideator_docs`</td>
</tr>
<tr>
<td>IDs in code</td>
<td>uuid4, string representation</td>
<td>`idea_id: str`, `run_id: str`</td>
</tr>
</table>
---
## 2. Migrations and Data Compatibility
### Schema Version Tracking
- Maintain a `schema_meta` table with a single row: `version INTEGER NOT NULL`.
- On every app startup, read the current version and run any pending migration scripts sequentially until reaching the latest version.
- Never skip or batch-apply migrations out of order.
### Migration File Conventions
- Location: `migrations/` directory in project root.
- Format: `{NNNN}_{short_description}.sql`, e.g., `0001_init.sql`, `0002_add_reports_table.sql`.
- Each file contains SQL that moves the schema from version N-1 to N.
- Files are append-only after they have shipped in any release. Never modify an existing migration file.
- Every migration must be idempotent where possible (use `IF NOT EXISTS`, `IF EXISTS` guards).
### Backwards Compatibility Within v0.x
- New columns must be nullable or have a safe default so existing rows are not broken.
- Column drops and type changes require a migration that preserves or transforms existing data.
- Renaming a column requires adding the new column, backfilling, then dropping the old in a follow-up migration (never in one step).
### ADR Reference
- Aligns with ADR-005 (SQLite as canonical store).
---
## 3. Fixtures and Reproducibility
### Seed Data
- Location: `fixtures/` directory.
- Format: YAML files, one per fixture set (e.g., `fixtures/example_ideas.yaml`).
- Contents: a small set of example ideas with known expected signal-collection and report outcomes.
- A CLI command `load-fixtures` seeds the DB in development and test environments from the fixtures directory.
- Fixtures are versioned (v1, v2, ...) in their filenames once stabilised: `fixtures/example_ideas_v1.yaml`.
- Fixtures are immutable after first use in an automated test suite. Changes require a new fixture version.
### Deterministic Test Runs
- In automated tests, always pin:
	- Prompt version (e.g., `analysis_v1.0.0.txt`).
	- Model name and parameters (temperature, top_p, seed if provider supports it).
	- Signal source: use a mocked or recorded signal set rather than live Tavily/Reddit calls.
- Tests must not make live external API calls unless explicitly tagged `@live` and skipped in CI by default.
---
## 4. Prompt and Model Versioning
### Prompt File Conventions
- Location: `prompts/` directory in project root.
- One plain text file per prompt, per version: `{role}_v{major}.{minor}.{patch}.txt`.
```javascript
prompts/
  analysis_v1.0.0.txt
  synthesis_v1.0.0.txt
  signal_query_v1.0.0.txt
```
- Each file contains only the prompt text. No code, no JSON, no metadata embedded in the file.
- Model name, temperature, top_p, and max_tokens for each prompt are specified in the YAML model routing config (`config/model_routing.yaml`), not in the prompt file itself.
### Versioning Rules
- Version format: `{major}.{minor}.{patch}`.
	- **Major**: structural changes (new required sections, new scoring dimensions, changed output format).
	- **Minor**: behaviour tweaks (wording changes, new examples, tone adjustments).
	- **Patch**: typo fixes and minor clarifications that do not change output behaviour.
- Once a prompt version ships in any release, its file is immutable. New changes create a new version file.
- Old prompt versions are retained in `prompts/` (never deleted) for reproducibility.
### Prompt Registry in Config
- `config/model_routing.yaml` maps each (role, tier, mode) to a prompt version, model, and parameters:
```yaml
roles:
  analysis:
    low:
      prompt: analysis_v1.0.0
      model: ollama/mistral:7b
      temperature: 0.2
      max_tokens: 1024
    medium:
      prompt: analysis_v1.0.0
      model: openai/gpt-4o-mini
      temperature: 0.2
      max_tokens: 2048
  synthesis:
    low:
      prompt: synthesis_v1.0.0
      model: ollama/mistral:7b
      temperature: 0.3
      max_tokens: 2048
    medium:
      prompt: synthesis_v1.0.0
      model: openai/gpt-4o-mini
      temperature: 0.3
      max_tokens: 4096
```
- Changing a model or prompt version in config is a **minor release** at minimum.
- Every run log entry records the prompt version and model name (not the full prompt text) for future reproducibility.
### ADR Reference
- Aligns with ADR-006 (LiteLLM as model abstraction).
---
## 5. Error Code Catalog Policy
### Error Code Format
- Pattern: `AE-{DOMAIN}-{NNN}` where:
	- `AE` = AIdeator Error prefix.
	- `DOMAIN` = one of the five domains below.
	- `NNN` = zero-padded 3-digit sequential number within that domain.
### Error Domains
<table header-row="true">
<tr>
<td>Domain Code</td>
<td>Domain Name</td>
<td>Example Codes</td>
</tr>
<tr>
<td>INPUT</td>
<td>Input validation failures</td>
<td>AE-INPUT-001, AE-INPUT-002</td>
</tr>
<tr>
<td>DEP</td>
<td>External dependency failures</td>
<td>AE-DEP-001, AE-DEP-002</td>
</tr>
<tr>
<td>RESOURCE</td>
<td>Timeouts, OOM, resource exhaustion</td>
<td>AE-RESOURCE-001</td>
</tr>
<tr>
<td>MODE</td>
<td>Runtime mode boundary violations</td>
<td>AE-MODE-001</td>
</tr>
<tr>
<td>ENGINE</td>
<td>Internal engine / unexpected errors</td>
<td>AE-ENGINE-001</td>
</tr>
</table>
### Starter Catalog
<table header-row="true">
<tr>
<td>Code</td>
<td>Domain</td>
<td>Description</td>
</tr>
<tr>
<td>AE-INPUT-001</td>
<td>INPUT</td>
<td>Missing required field in POST /ideas or POST /runs</td>
</tr>
<tr>
<td>AE-INPUT-002</td>
<td>INPUT</td>
<td>idea_id not found when creating a run</td>
</tr>
<tr>
<td>AE-INPUT-003</td>
<td>INPUT</td>
<td>Invalid tier or mode value</td>
</tr>
<tr>
<td>AE-DEP-001</td>
<td>DEP</td>
<td>Tavily API timeout or connection error</td>
</tr>
<tr>
<td>AE-DEP-002</td>
<td>DEP</td>
<td>Reddit API rate limit exceeded</td>
</tr>
<tr>
<td>AE-DEP-003</td>
<td>DEP</td>
<td>LLM provider timeout or connection error</td>
</tr>
<tr>
<td>AE-RESOURCE-001</td>
<td>RESOURCE</td>
<td>Validation run timed out (exceeded max duration)</td>
</tr>
<tr>
<td>AE-MODE-001</td>
<td>MODE</td>
<td>Outbound call attempted in local-only mode</td>
</tr>
<tr>
<td>AE-ENGINE-001</td>
<td>ENGINE</td>
<td>Unhandled exception in LangGraph node</td>
</tr>
<tr>
<td>AE-ENGINE-002</td>
<td>ENGINE</td>
<td>SQLite write failure</td>
</tr>
</table>
### Rules
- Every non-2xx HTTP response includes: `error_code`, `error_domain`, `message` (user-facing), `run_id` (if applicable).
- User-facing `message` is short, non-technical, and contains no secrets, stack traces, or idea content.
- Log entries use `error_code` + internal detail for debugging. Internal detail must not contain secrets or idea content (NO-003).
- New error codes are append-only within their domain. Codes are never reused or renumbered.
---
## 6. Signal Source Defaults (Closes AQ-001 and AQ-002)
### Default Subreddit List (AQ-001)
The following subreddits are queried by default in PH-A signal collection. They can be overridden in config:
```yaml
signal_sources:
  reddit:
    default_subreddits:
      - startups
      - SideProject
      - Entrepreneur
      - indiehackers
      - microsaas
    max_results_per_subreddit: 5
```
Rationale: These communities represent the primary target user (Reddit-native builders) and produce high-signal startup discussion.
### Hybrid Mode Search Query Semantics (AQ-002)
- In `hybrid` mode, the search query sent to Tavily and Reddit contains **keywords and search terms only** — derived from the idea title and target user.
- The full idea description, context, and target user prose are **never sent** to external APIs in hybrid mode.
- A short (max 10-word) keyword query is generated locally by the SignalCollector before making any outbound call.
- This convention must be reflected in the mode_disclosure text for `hybrid` mode (see 07 Spec and Flows).
---
## 7. Backup and Restore Runbook
### What to Back Up
<table header-row="true">
<tr>
<td>Artifact</td>
<td>Location</td>
<td>Canonical?</td>
<td>Backup Priority</td>
</tr>
<tr>
<td>SQLite database</td>
<td>db/aideator.db</td>
<td>Yes</td>
<td>Required</td>
</tr>
<tr>
<td>Prompt files</td>
<td>prompts/</td>
<td>Yes</td>
<td>Required</td>
</tr>
<tr>
<td>Model routing config</td>
<td>config/model_routing.yaml</td>
<td>Yes</td>
<td>Required</td>
</tr>
<tr>
<td>Markdown artifacts</td>
<td>docs/</td>
<td>Derived</td>
<td>Optional (rebuildable)</td>
</tr>
<tr>
<td>Log files</td>
<td>logs/</td>
<td>No</td>
<td>Optional</td>
</tr>
</table>
### Backup Steps
1. Stop the app or ensure no active write transactions are in progress.
2. Copy `db/aideator.db` to backup location (e.g., `backups/aideator_YYYYMMDD.db`).
3. Copy `prompts/` and `config/model_routing.yaml` to backup location.
4. Optionally copy `docs/` for convenience.
### Restore Steps
1. Stop the app.
2. Replace `db/aideator.db` with the backed-up file.
3. Restore `prompts/` and `config/model_routing.yaml` if needed.
4. Restart the app — migrations will run automatically if the schema version is behind the code version.
5. If `docs/` is missing or incomplete, run: `python manage.py rebuild-docs --all` to regenerate all markdown artifacts from DB.
### Export
- Run `python manage.py export-json --output backups/export_YYYYMMDD.ndjson` to dump all ideas, runs, signals, and reports as NDJSON.
- This file is portable and importable without the SQLite DB.
- Aligns with NO-005 (export guarantee).
---
## 8. Release and Upgrade Policy
### Version Format
- App versions follow `v{major}.{minor}.{patch}` SemVer.
- Within `v0.x`, breaking changes are permitted but must:
	- Be documented in `CHANGELOG.md` under `Breaking Changes`.
	- Ship with a migration script.
	- Include updated README upgrade instructions.
### Git Branch and Tag Strategy
- `main` = latest stable, always releasable.
- `feat/{name}` = feature branches, merged to main via PR.
- `fix/{name}` = bug fix branches.
- Release tags: `v0.1.0`, `v0.2.0`, etc. on `main`.
- No long-lived `dev` branch; use feature branches and merge frequently.
### Commit Message Format
```javascript
<type>(<scope>): <short summary under 72 chars>

Body (optional): what and why, not how.
Footer: refs FR-*, NFR-*, ADR-*, AE-* if applicable.
```
Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `migration`.
Examples:
- `feat(engine): add SignalCollector node with Tavily integration` (refs FR-003)
- `migration(db): add reports table` (refs 0002_add_reports.sql)
- `fix(mode-guard): block outbound calls in local-only mode` (refs AE-MODE-001, INV-001)
### Changelog Policy
- Maintain `CHANGELOG.md` with sections per release: `Added`, `Changed`, `Fixed`, `Removed`, `Migrations`, `Breaking Changes`.
- Every release entry includes:
	- Prompt version changes (if any).
	- Schema migrations applied.
	- Changes to runtime modes or data boundary behaviour.
	- New or changed error codes.
### Upgrade Compatibility Rule
- Supported upgrade path is always: pull new version → run migrations (automatic at startup) → restart.
- Users must never be required to perform manual DB surgery for any supported upgrade path.
- If manual steps are unavoidable, they must be documented in the release notes with exact commands.
---
## 9. Alignment with NON_OBVIOUS Decisions
<table header-row="true">
<tr>
<td>NON_OBVIOUS</td>
<td>Convention That Enforces It</td>
</tr>
<tr>
<td>NO-001: Storage layout</td>
<td>Section 7 defines db/, docs/, logs/ locations and backup priority.</td>
</tr>
<tr>
<td>NO-002: Canonical vs derived</td>
<td>Section 2 and Section 7 both state DB is canonical; docs/ is rebuildable.</td>
</tr>
<tr>
<td>NO-003: Telemetry stance</td>
<td>Section 5 error code rules prohibit idea content in log messages.</td>
</tr>
<tr>
<td>NO-004: Network bind default</td>
<td>Documented in README and docker-compose defaults (127.0.0.1). Enforced in PH-C packaging.</td>
</tr>
<tr>
<td>NO-005: Export guarantee</td>
<td>Section 7 export-json command defined.</td>
</tr>
<tr>
<td>NO-006: local-only is first-class</td>
<td>Section 6 hybrid mode semantics ensure local-only is fully functional.</td>
</tr>
<tr>
<td>NO-007: Rebuild safety</td>
<td>Section 7 rebuild-docs command is additive only; never touches DB rows.</td>
</tr>
<tr>
<td>NO-008: No hidden network calls</td>
<td>All outbound endpoints defined in config. No hardcoded URLs. Enforced by Mode Guard.</td>
</tr>
<tr>
<td>NO-009: Config over code</td>
<td>Section 4 model routing YAML contains all provider/model/prompt bindings.</td>
</tr>
<tr>
<td>NO-010: Mode is immutable per run</td>
<td>Mode set at POST /runs creation; no update endpoint exposed.</td>
</tr>
<tr>
<td>NO-011: Cursor notes mandatory</td>
<td>Section 4 prompt versioning ensures synthesis prompt always includes Cursor/Claude notes template.</td>
</tr>
<tr>
<td>NO-012: Card citations mandatory</td>
<td>Section 5 error codes include AE-ENGINE-001 to catch malformed reports at synthesis time.</td>
</tr>
</table>
---
## 10. Notion Workflow Rules
- Never delete pages; set Status = Archived.
- Version bumps on every substantive edit (update the Version field in Metadata).
- All changes post-freeze go through the Change Requests page.
- IDs (FR-*, NFR-*, ADR-*, AE-*) are append-only and never reused.
---
## Conflicts or Gaps
<table header-row="true">
<tr>
<td>ID</td>
<td>Item</td>
<td>Status</td>
</tr>
<tr>
<td>GAP-001</td>
<td>AQ-001 (subreddit list)</td>
<td>Closed in Section 6 of this page.</td>
</tr>
<tr>
<td>GAP-002</td>
<td>AQ-002 (hybrid mode search query semantics)</td>
<td>Closed in Section 6 of this page.</td>
</tr>
<tr>
<td>GAP-003</td>
<td>LiteLLM token callback support across providers</td>
<td>Open — to be confirmed in PH-A spike. Log as best-effort if unavailable.</td>
</tr>
<tr>
<td>GAP-004</td>
<td>Local LLM latency on reference hardware</td>
<td>Open — to be confirmed in PH-A spike before NFR-001 is frozen.</td>
</tr>
</table>
