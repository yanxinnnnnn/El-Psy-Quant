FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-runtime.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements-runtime.txt

COPY pyproject.toml README.md alembic.ini ./
COPY src ./src
COPY examples/demo_workspace ./examples/demo_workspace
RUN python -m pip install --no-cache-dir --no-deps .

COPY scripts/docker_backend_healthcheck.py ./scripts/docker_backend_healthcheck.py

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

USER appuser

EXPOSE 8000

CMD ["el-psy-quant", "start-local-backend", "--mode", "standard", "--workspace-root", "/data", "--alembic-config", "/app/alembic.ini"]
