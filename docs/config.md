# Runtime config

AIdeator reads environment values from process env and optional `.env` at repo root.

## Variables

- `APP_ENV`: `local|dev|prod`. Controls reload and environment labeling.
- `APP_HOST`: bind host for local run/uvicorn.
- `APP_PORT`: bind port for local run/uvicorn.
- `APP_DB_URL`: database URL (currently reserved for storage backend wiring).
- `APP_DOCS_DIR`: output/read path for markdown report docs.
- `APP_DEFAULT_MODE`: `local|hybrid|cloud` (mapped to run modes `local-only|hybrid|cloud-enabled`).
- `DEFAULT_MODE`: legacy alias; kept for compatibility.
- `TAVILY_API_KEY`: Tavily external signal adapter key.
- `REDDIT_CLIENT_ID`: Reddit API client id.
- `REDDIT_CLIENT_SECRET`: Reddit API secret.
- `LLM_API_BASE`: optional custom LLM gateway/base URL.
- `LLM_API_KEY`: LLM API key for cloud providers.
- `LOG_LEVEL`: `debug|info|warn|error`.
- `LOG_JSON`: `true|false`, emits JSON logs when true.

## Modes

- `local-only`:
  - Set `APP_DEFAULT_MODE=local`.
  - No outbound network calls for run-mode protected paths.
  - Keep external provider keys empty.
- `hybrid`:
  - Set `APP_DEFAULT_MODE=hybrid`.
  - Allows curated external signal calls with keyword-only payload semantics.
- `cloud-enabled`:
  - Set `APP_DEFAULT_MODE=cloud`.
  - Enables full external mode (provider keys/base should be configured).

## Overrides

- `.env` defines defaults for local development.
- Environment variables override `.env` values.
- CLI flags override both when invoking uvicorn directly, e.g.:
  - `uvicorn api.app:app --host 0.0.0.0 --port 9000`

## Logging and inspection

Logs are emitted to stdout/stderr only. In containers, inspect with `docker logs`; on services, use `journalctl` (or service manager logs).

Example events:

- App startup:
  - `event=app_startup env=local host=0.0.0.0 port=8000 default_mode=local-only`
- Run creation:
  - `event=run_created run_id=<id> idea_id=<id> mode=local-only tier=low`
- Run success/failure:
  - `event=run_succeeded run_id=<id> duration_ms=<n>`
  - `event=run_failed run_id=<id> duration_ms=<n>`
