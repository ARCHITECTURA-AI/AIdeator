FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=prod \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

COPY pyproject.toml requirements.txt README.md LICENSE ./

RUN python -m pip install --upgrade pip \
 && python -m pip install -r requirements.txt

COPY aideator ./aideator
COPY api ./api
COPY adapters ./adapters
COPY cmd ./cmd
COPY db ./db
COPY engine ./engine
COPY infra ./infra
COPY models ./models
COPY templates ./templates
COPY static ./static
COPY docs ./docs
COPY main.py ./main.py

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
