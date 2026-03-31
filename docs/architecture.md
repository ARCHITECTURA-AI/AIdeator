# AIdeator architecture overview

AIdeator is organized around an execution pipeline that validates a product idea, tracks run state, and emits markdown artifacts for human review.

## Core pipeline

- Idea is created through API or UI (`POST /ideas`).
- Run is created with mode + tier (`POST /runs`) and moved through lifecycle (`pending -> running -> succeeded|failed`).
- Orchestrator executes validations and synthesizes cards.
- Report data is persisted in repository storage and rendered as markdown docs (`docs/idea-{id}.md`).

Flow summary:

- Idea -> Run -> Orchestrator -> Cards/Report -> Markdown artifact

## Modes and tiers

- Modes:
  - `local-only`: no outbound HTTP; local filesystem and local model endpoints only.
  - `hybrid`: curated external calls allowed with keyword-only semantics.
  - `cloud-enabled`: full external integrations allowed by configured providers.
- Tiers:
  - `low`, `medium`, `high` represent validation intensity/routing depth.

Configuration mapping:

- `APP_DEFAULT_MODE=local|hybrid|cloud` maps to run modes `local-only|hybrid|cloud-enabled`.
- Runtime env config is centralized in `api/config.py`.

## Main modules

- `api/`
  - FastAPI app bootstrap, routers, middleware, health endpoints.
- `engine/`
  - Run orchestration and lifecycle transitions.
- `db/`
  - Idea/run/report repositories and snapshot import/export helpers.
- `cmd/`
  - Operational commands like docs rebuild.
- `infra/`
  - Logging helpers and guardrail utilities.
- `aideator/`
  - Packaging metadata and CLI entrypoints.

## Runtime surfaces

- HTTP API via FastAPI (`api.app:app`).
- CLI:
  - `aideator serve`
  - `aideator rebuild-docs`
- Docker:
  - `Dockerfile` for app image.
  - `docker-compose.yml` for app + optional local LLM service.
