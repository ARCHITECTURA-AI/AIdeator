.PHONY: dev test lint run-local-only

dev:
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

test:
	python -m pytest -q

lint:
	python -m ruff check .

run-local-only:
	APP_ENV=local APP_DEFAULT_MODE=local uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
