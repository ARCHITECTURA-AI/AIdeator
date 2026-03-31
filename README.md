<p align="center">
  <img src="logo.png" alt="AIdeator logo" width="200" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AIdeator-Idea%20Validation%20Engine-4F46E5?style=for-the-badge" alt="AIdeator" />
</p>

<h1 align="center">AIdeator</h1>

<p align="center">
  <b>Local-first FastAPI service for idea validation, run orchestration, and markdown reports</b>
</p>

<p align="center">
  <i>Create ideas, execute runs by privacy mode, and review generated reports without extra tooling.</i>
</p>

<br/>

<p align="center">
  <img src="https://img.shields.io/badge/Setup-2%20Minutes-22C55E?style=flat-square" alt="Setup time" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.116%2B-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker compose" />
  <img src="https://img.shields.io/badge/Reports-Markdown-6366F1?style=flat-square" alt="Markdown reports" />
</p>

<p align="center">
  <a href="docs/architecture.md"><b>Website</b></a> ·
  <a href="docs/config.md"><b>Docs</b></a> ·
  <a href="#installation"><b>Getting Started</b></a> ·
  <a href="../../issues"><b>Issues</b></a> ·
  <a href="docs/release-checklist.md"><b>Release Ops</b></a>
</p>

<p align="center">
  <a href="docs/config.md"><b>Config guide</b></a> ·
  <a href="#running-locally"><b>Quick start</b></a> ·
  <a href="docs/architecture.md"><b>Architecture</b></a> ·
  <a href="docs/security-privacy.md"><b>Security & Privacy</b></a> ·
  <a href="CONTRIBUTING.md"><b>Contributing</b></a>
</p>

<br/>

AIdeator is a FastAPI-based idea validation service that turns raw product ideas into reproducible run records and markdown reports. It provides a consistent flow for creating ideas, launching validation runs, and reviewing generated artifacts under `docs/`.

The core runtime model is simple: an idea is submitted, a run executes under a chosen privacy mode/tier, and the engine synthesizes report cards that can be rendered into markdown. This keeps execution auditable and easy to run in local dev, CI, and containers.

The project is designed for gradual hardening: local-first defaults, explicit mode configuration (`local-only`, `hybrid`, `cloud-enabled`), and container-friendly stdout/stderr logs.

## Features

- Privacy modes: `local-only`, `hybrid`, `cloud-enabled`
- Idea -> run lifecycle with status polling
- Markdown report artifacts (`docs/idea-{id}.md`)
- FastAPI API plus simple server-rendered web pages
- CLI for serving and rebuilding docs

## Architecture at a glance

- `api/`: FastAPI app bootstrap, routes, middleware, health checks
- `engine/`: run orchestration and lifecycle execution
- `db/`: repository layer for ideas/runs/reports
- `cmd/`: operational commands (docs rebuild)
- `aideator/`: package metadata and CLI entrypoints

Detailed overview: `docs/architecture.md`

## Installation

From source:

```bash
git clone https://github.com/ARCHITECTURA-AI/AIdeator
cd AIdeator
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
```

Alternative dev install:

```bash
pip install -r requirements.txt
```

## Running locally

Using Makefile:

```bash
make dev
make run-local-only
```

Using CLI:

```bash
aideator serve
```

Default URL: `http://localhost:8000`  
Health check: `http://localhost:8000/healthz`

## Docker usage

Build and run:

```bash
docker build -t your-org/aideator:latest .
docker run --rm -p 8000:8000 --env-file .env your-org/aideator:latest
```

With compose:

```bash
docker compose up
```

(`docker-compose up` also works on installations that still use the legacy binary.)

Mode selection is env-driven:

- `APP_DEFAULT_MODE=local` -> local-only
- `APP_DEFAULT_MODE=hybrid` -> hybrid
- `APP_DEFAULT_MODE=cloud` -> cloud-enabled

## CLI commands

- `aideator serve`
  - Starts `api.app:app` via uvicorn using env/config defaults.
  - Supports `--host`, `--port`, and `--reload`.
- `aideator rebuild-docs`
  - Rebuilds markdown report artifacts for succeeded runs into `APP_DOCS_DIR`.

Also available as direct script entrypoints:

- `aideator-serve`
- `aideator-rebuild-docs`

## Development workflow

```bash
make lint
make test
make dev
```

Example seed flow:

1. Start app in local-only mode:

```bash
make run-local-only
```

1. In another terminal:

```bash
python scripts/seed_example.py
```

This creates a sample idea, runs local-only validation, and prints IDs + report path.  
Generated reports are under `docs/idea-{id}.md`.

## Configuration

- Copy `.env.example` to `.env` and adjust values.
- Config reference: `docs/config.md`
- Security/privacy reference: `docs/security-privacy.md`

Key vars:

- `APP_DB_URL`, `APP_DOCS_DIR`
- `APP_DEFAULT_MODE`
- `TAVILY_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `LLM_API_BASE`, `LLM_API_KEY`
- `LOG_LEVEL`, `LOG_JSON`

## Security and privacy

Local-only mode is designed to avoid outbound third-party HTTP calls by default run policy.  
See `docs/security-privacy.md` for guarantees, caveats, and org hardening guidance.

## Releases and change management

- Release process: `docs/release-checklist.md`
- Change history: `CHANGELOG.md`
- Contribution process: `CONTRIBUTING.md`

Version mapping:

- `0.1.0` -> PH-A
- `0.2.0` -> PH-B
- `0.3.0` -> PH-C
- `0.4.0` -> PH-D

## License

MIT. See `LICENSE`.