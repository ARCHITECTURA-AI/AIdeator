# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog and this project uses Semantic Versioning while mapping release phases:

- `0.1.0` -> PH-A
- `0.2.0` -> PH-B
- `0.3.0` -> PH-C
- `0.4.0` -> PH-D

## [Unreleased]

### Added

- Packaging CLI entrypoints (`aideator`, `aideator-serve`, `aideator-rebuild-docs`).
- Containerized local stack (`Dockerfile`, `docker-compose.yml` with optional local LLM).
- Release and ops docs (`docs/release-checklist.md`, `docs/architecture.md`, `docs/security-privacy.md`).

### Changed

- Runtime/readme docs now align with env-based config and make targets.
- Version source is centralized in `aideator/__init__.py`.

## [0.1.0] - 2026-03-31

### Added

- Initial PH-A baseline for idea/run/report flow (FR-001, ADR-001).

