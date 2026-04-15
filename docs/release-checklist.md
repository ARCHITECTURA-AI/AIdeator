# Release Checklist

## Pre-release Validation

### Code Quality
- [ ] Run linter: `make lint` or `ruff check .`
- [ ] Run formatter: `ruff format --check .`
- [ ] Run type checks: `python -m mypy api engine models db adapters infra cmd aideator`

### Tests
- [ ] Unit tests: `python -m pytest tests/unit/ -v`
- [ ] E2E tests: `python -m pytest tests/e2e/ -v`
- [ ] Smoke tests: `python -m pytest tests/smoke/ -v`
- [ ] Contract tests: `python -m pytest tests/contract/ -v`
- [ ] Full suite: `python -m pytest tests/ --ignore=tests/performance --ignore=tests/security -v`
- [ ] All tests pass with **zero failures**

### Application Smoke Test
- [ ] Start server: `aideator serve`
- [ ] Health check: `curl http://localhost:8000/healthz` → 200
- [ ] Dashboard loads: `http://localhost:8000/app/dashboard`
- [ ] Create idea via UI
- [ ] Run validation (local-only mode)
- [ ] View HTML report
- [ ] Print to PDF (browser print dialog)
- [ ] Config show: `aideator config show`

### Search & LLM Integration
- [ ] Built-in search: URL fetch works
- [ ] Tavily search (if key available): returns results
- [ ] Exa search (if key available): returns results
- [ ] Ollama LLM (if running): healthcheck passes
- [ ] Cloud LLM (if configured): healthcheck passes

## Version Bump

- [ ] Update version in `aideator/__init__.py` (`__version__`)
- [ ] Confirm `pyproject.toml` reads version dynamically
- [ ] Update `CHANGELOG.md` with release date and notable changes

## Documentation

- [ ] `README.md` reflects current feature set
- [ ] `docs/config.md` covers all environment variables and config options
- [ ] `docs/security-privacy.md` has correct privacy mode guarantees
- [ ] `docs/architecture.md` matches codebase structure

## Tag and Push

```bash
git add -A
git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

## Build and Publish Docker Image

```bash
docker build -t your-org/aideator:vX.Y.Z .
docker build -t your-org/aideator:latest .
docker push your-org/aideator:vX.Y.Z
docker push your-org/aideator:latest
```

## Build and Publish Python Package (Optional)

```bash
python -m pip install build twine
python -m build
twine upload dist/*
```

## Post-release

- [ ] Verify Docker image runs: `docker run --rm -p 8000:8000 your-org/aideator:vX.Y.Z`
- [ ] Update landing page / waitlist if applicable
- [ ] Notify stakeholders
