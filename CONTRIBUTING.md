## Contributing

Thank you for considering a contribution to AIdeator.

### Development Setup

- Python 3.10
- Install in editable mode with dev tools:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy api engine models db adapters infra cmd
```

### Changes and Scope

- Keep changes within the locked scope in `docs/scope-lock.md`.
- Do not add business logic that introduces new `FR-*` / `NFR-*` / `INV-*` / `SAFE-*` IDs without updating the docs.
- Prefer small, focused PRs.

### Tests and Lint

- Add or update tests under `tests/` for any behavior changes.
- Ensure:
  - `pytest` passes
  - `ruff check .` is clean
  - `mypy api engine models db adapters infra cmd` is clean

### Commit Messages

- Follow the conventions in `docs/conventions.md` (e.g. `feat(engine): ...`, `fix(api): ...`).

