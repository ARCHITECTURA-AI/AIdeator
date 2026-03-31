# Release checklist

## Pre-release validation

- Run lint: `make lint`
- Run tests: `make test`
- Run type checks (if used in release gate): `python -m mypy api engine models db adapters infra cmd aideator`
- Smoke run app: `aideator serve` and `curl http://localhost:8000/healthz`

## Version bump

- Update version in `aideator/__init__.py` (`__version__`).
- Confirm `pyproject.toml` still reads version dynamically from `aideator/__init__.py`.
- Update `CHANGELOG.md` with release date and notable changes.

## Tag and push

- `git tag vX.Y.Z`
- `git push origin vX.Y.Z`

## Build and publish Docker image

- `docker build -t your-org/aideator:vX.Y.Z .`
- `docker push your-org/aideator:vX.Y.Z`

## Build and publish Python artifact (optional)

- `python -m pip install build twine`
- `python -m build`
- `twine upload dist/*`
