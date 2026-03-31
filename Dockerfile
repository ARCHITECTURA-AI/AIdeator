FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md ./ 
COPY api ./api

RUN python -m pip install --upgrade pip \
 && python -m pip install "fastapi>=0.116.0" "uvicorn[standard]>=0.35.0"

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
