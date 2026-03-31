### 1. Runtime & Ops basics

- **Environment & config**
  - `.env.example` with all required vars (ports, DB path, model endpoints, API keys).
  - Clear config docs: how to run in `local-only`, `hybrid`, `cloud-enabled` from env/file.

- **Process entrypoint**
  - Single `uvicorn`/`gunicorn` (or equivalent) entry script for Docker and local dev.
  - Healthcheck endpoint (`/healthz` or `/status`) for Docker/Kubernetes.

- **Logging & metrics wiring**
  - Make sure the logging/telemetry you planned is actually wired to stdout/stderr for containers, and documented so users know how to inspect runs.

### 2. Developer experience

- **Top-level dev commands**
  - `make dev`, `make test`, `make lint`, `make run-local-only`.
  - Short “workflow” section in README: clone → create venv → run tests → start app → hit example curl.

- **Seed scripts / example data**
  - One small script or notebook that:
    - creates a sample idea,
    - runs a local-only validation,
    - shows where the `docs/idea-{id}.md` ended up.

### 3. User-facing surfaces

You already mentioned:

- **Internal frontend** (operator UI)
  - Minimal run dashboard: create idea, trigger run, see status, see cards + markdown.
  - Mode/tier selector, but constrained to PH‑A/PH‑B scope.

- **Marketing / landing page**
  - Positioning: “local-first idea validation engine.”
  - Very explicit about privacy modes and local-only guarantees.
  - Link to: docs, GitHub repo, quickstart, and maybe a short “how it works” diagram.

Additional UX you likely want:

- **Docs viewer**
  - Even a simple in-app markdown viewer or static docs directory browser for `docs/idea-{id}.md`, so users don’t have to drop into VS Code to read reports.

### 4. Distribution and packaging

- **Docker**
  - App image (what you already plan).
  - Optional: docker-compose with:
    - app,
    - local LLM (Ollama or similar),
    - any other needed service.

- **Python packaging**
  - `pyproject.toml` / `setup.cfg` so it can be installed as a CLI (`aideator serve`, `aideator rebuild-docs`).
  - Versioning scheme aligned with your PH‑A/B/C/D phases.

- **Release artifacts**
  - A “Release checklist” in docs: which tests to run, which tags to push, how to publish image.

### 5. Documentation & governance

- **Architecture / system overview doc**
  - A short `docs/architecture.md` that’s less dense than the planning pages but explains:
    - core pipeline,
    - modes/tiers,
    - main modules.

- **Security & privacy note**
  - 1–2 pages explicitly documenting:
    - what “local-only” guarantees,
    - what telemetry exists,
    - how to configure/disable external calls.

- **Change management**
  - A lightweight `CHANGELOG.md` tied to your FR/INV/ADR IDs.
  - Note how to request changes post‑freeze (CR‑* process) for external contributors.
