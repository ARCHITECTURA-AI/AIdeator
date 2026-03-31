## Changelog

### Unreleased

- Initial scaffold:
  - Added `pyproject.toml` with FastAPI, pytest, ruff, mypy.
  - Created architecture-aligned packages: `api/`, `engine/`, `models/`, `db/`, `adapters/`, `infra/`, `cmd/`.
  - Added layered test directories and a smoke test.
  - Wired CI workflow for lint, type-check, and tests.
  - Mirrored planning docs under `docs/` and added execution/scope lock files.

