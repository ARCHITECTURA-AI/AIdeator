# Security and privacy

## Local-only guarantees

When runs execute in `local-only` mode:

- External HTTP calls are blocked by mode guardrails.
- Idea processing stays on local runtime components.
- Data is stored locally in configured paths:
  - DB URL/path from `APP_DB_URL`
  - Markdown reports in `APP_DOCS_DIR` (default `./docs`)

Caveats:

- Logs can include run IDs, paths, statuses, and operational metadata.
- Avoid writing secrets into idea content if logs are shared.

## Telemetry and logging

AIdeator logs are process-local by default:

- Request logs (`method`, `path`, `status`, `duration_ms`)
- Run lifecycle logs (`run_created`, `run_started`, `run_succeeded`, `run_failed`)
- Error logs include stack traces at `ERROR` level

Defaults:

- Logs go to stdout/stderr.
- No remote telemetry exporter is configured by default.

Configuration:

- `LOG_LEVEL=debug|info|warn|error`
- `LOG_JSON=true|false` for machine-readable log format

## External calls and controls

Potential external integrations:

- Tavily (`TAVILY_API_KEY`)
- Reddit (`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`)
- LLM provider (`LLM_API_BASE`, `LLM_API_KEY`)

Hardening guidance:

- For fully offline operation:
  - Set `APP_DEFAULT_MODE=local`
  - Keep external API keys empty
  - Enforce network egress controls at host/container level
- For `hybrid`:
  - Use scoped API keys
  - Restrict allowed destinations with firewall/network policy
- For `cloud-enabled`:
  - Treat run payloads as potentially externalized data
  - Use least-privilege keys and short key rotation windows

## Team/org recommendations

- Run with container runtime isolation where possible.
- Store secrets outside source control (`.env`, secret manager, CI vault).
- Centralize logs in approved internal observability systems only.
- Review mode defaults before release (`APP_DEFAULT_MODE` and env files).
