# Sprint 138 — Application Service and API Skeleton

## Status

Complete.

## Objective

Begin Milestone 26 with a small local FastAPI application boundary and versioned API skeleton.

## Delivered

- public deterministic `create_app()` factory and module-level ASGI `app`
- explicit `/api/v1` route boundary
- exact process-health response at `GET /api/v1/health`
- explicit Pydantic health and error schemas
- server-owned UUID request IDs stored on request state and returned in `X-Request-ID`
- stable error codes for not found, method not allowed, request validation, other HTTP errors, and unexpected failures
- sanitized HTTP 500 responses without traceback or exception detail exposure
- loopback-only local run documentation

## Health Contract

```json
{
  "status": "ok",
  "service": "el-psy-quant",
  "api_version": "v1"
}
```

This is application-process health only. It makes no claim about artifacts, databases, workers, brokers, QMT, market data, external services, live trading, or deployment readiness.

## Local Run

```text
uv run uvicorn el_psy_quant.api.app:app --host 127.0.0.1 --port 8000
```

## Scope Boundary

Sprint 138 adds no strategy catalog or detail behavior, artifact inspection, paper-run commands, lifecycle commands, persistence, repositories, background jobs, authentication, CORS, Web UI, Docker, configured workflow changes, arbitrary filesystem access, broker or QMT integration, live execution, automatic approval, or capital allocation.

## Next Step

```text
Sprint 139 — Strategy Catalog and Detail Read Services
```
