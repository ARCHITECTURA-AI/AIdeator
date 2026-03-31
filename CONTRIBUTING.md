# Contributing

Thanks for contributing to AIdeator.

## Basic flow

1. Fork and clone.
2. Create a branch from `main`.
3. Implement focused changes with tests/docs.
4. Open a PR with clear scope and verification notes.

## Local dev checks

- `make lint`
- `make test`
- Optional type-check pass:
  - `python -m mypy api engine models db adapters infra cmd aideator`

## Change management

For user-visible or architectural changes:

- Open/update an issue first.
- Reference IDs when relevant:
  - `FR-*` for feature requests
  - `INV-*` for investigations
  - `ADR-*` for architecture decisions
- Post-freeze or scope-exception changes must include a Change Request identifier (`CR-*`) in the issue/PR summary.

Maintainer review expectations:

- Update affected ADR docs if architecture changes.
- Keep `CHANGELOG.md` current for user-visible changes.
- Update docs (`README.md`, `docs/*.md`) when behavior/config/ops flows change.

## Commit conventions

- Follow `docs/conventions.md` commit style (e.g. `feat(api): ...`, `fix(engine): ...`).

