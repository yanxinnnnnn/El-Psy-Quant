FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md alembic.ini ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

COPY scripts/docker_backend_healthcheck.py ./scripts/docker_backend_healthcheck.py

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "mkdir -p /data/research /data/evidence /data/paper && python -m alembic upgrade head && exec python -m uvicorn el_psy_quant.api.app:app --host 0.0.0.0 --port 8000"]
