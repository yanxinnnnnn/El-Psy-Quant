FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements-build.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements-build.txt

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip wheel --no-cache-dir --no-deps --no-build-isolation \
    --wheel-dir /wheelhouse .

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-runtime.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements-runtime.txt

COPY --from=builder /wheelhouse /wheelhouse
RUN python -m pip install --no-cache-dir --no-deps \
    /wheelhouse/el_psy_quant-*.whl \
    && rm -rf /wheelhouse

COPY alembic.ini ./
COPY examples/demo_workspace ./examples/demo_workspace

COPY scripts/docker_backend_healthcheck.py ./scripts/docker_backend_healthcheck.py

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

USER appuser

EXPOSE 8000

CMD ["el-psy-quant", "start-local-backend", "--mode", "standard", "--workspace-root", "/data", "--alembic-config", "/app/alembic.ini"]
