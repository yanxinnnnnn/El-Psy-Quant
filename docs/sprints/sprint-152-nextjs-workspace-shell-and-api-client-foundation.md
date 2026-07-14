# Sprint 152 — Next.js Workspace Shell and API Client Foundation

## Status

Complete.

## Objective

Begin Milestone 28 with the smallest reviewable local Founder workspace shell,
same-origin transport, deterministic OpenAPI-derived TypeScript contract, and
typed API client needed by later Web sprints.

Sprint 152 proves only:

```text
Browser
  -> local Next.js workspace shell
  -> fixed same-origin /api/backend rewrite
  -> existing FastAPI /api/v1/health
```

## Frontend Repository Boundary

The repository keeps its Python `uv` project at the root and adds one independent
npm application under `web/`. It uses Node.js 24 LTS, a committed npm lockfile,
stable Next.js 16 with the App Router, strict TypeScript, and plain CSS. No root
JavaScript workspace or alternative package manager was added.

Install dependencies from the repository root:

```bash
uv sync
npm --prefix web ci
```

## Workspace Shell

The only implemented route is `/`. Its reusable responsive shell provides:

- El-Psy-Quant and local Founder-workspace identity
- accessible header, navigation, main, skip-link, labels, and focus behavior
- Overview as the only enabled destination
- explicit unavailable entries for the S153–S158 workspace areas
- process-health loading, available, and unavailable states
- a keyboard-operable manual connection retry

The shell contains no strategy, research, governance, paper-job, portfolio,
comparison, or lifecycle business data or actions.

## Same-Origin API Transport

Next.js reads one server-only setting:

```text
EL_PSY_QUANT_API_ORIGIN=http://127.0.0.1:8000
```

When absent, the value defaults to `http://127.0.0.1:8000`. Validation permits
only `http` or `https` with `127.0.0.1`, `localhost`, or `::1`. It rejects
credentials, remote hosts, non-root paths, queries, fragments, malformed URLs,
and surrounding whitespace. Configuration changes require restarting Next.js.

The browser never receives the backend origin. It calls only:

```text
/api/backend/api/v1/...
```

The transparent rewrite matches only `/api/backend/api/v1/:path*` and forwards
to `<validated-origin>/api/v1/:path*`. Paths such as `/api/backend/docs`,
`/api/backend/openapi.json`, and future unversioned backend routes are not
proxied. The rewrite adds no route handler, payload transformation, cache,
retry, polling, persistence, authorization, or business logic. FastAPI CORS
remains unchanged. Development and production Next.js commands bind to
`127.0.0.1` by default.

Local startup uses two terminals:

```bash
uv run uvicorn el_psy_quant.api.app:app --host 127.0.0.1 --port 8000
npm --prefix web run dev
```

## Generated API Contract

FastAPI OpenAPI remains the source of truth:

```text
side-effect-free create_app(...)
  -> deterministic app.openapi()
  -> web/src/generated/openapi.json
  -> openapi-typescript
  -> web/src/generated/api-types.ts
```

The Python exporter explicitly neutralizes research, evidence, product-database,
and paper-artifact environment settings before importing and constructing the
application. Export does not require a server or network and does not create,
open, migrate, or inspect local product resources.

Generate or check both committed artifacts:

```bash
npm --prefix web run contracts:generate
npm --prefix web run contracts:check
```

The generated files are derivative transport artifacts and are not independent
domain or API authority. Freshness failures stop the frontend and unified
quality gates.

## Typed Health Client

The native-fetch client exposes only the Sprint 152 health wrapper. Its fixed
base path is `/api/backend`; it has no arbitrary-origin or arbitrary-URL helper.
The wrapper consumes generated OpenAPI path and success types, validates the
runtime health payload, and preserves `X-Request-ID` when available.

Stable API envelopes become a bounded `ApiClientError` with HTTP status, public
code, public message, and optional request ID. Network, malformed JSON,
unexpected payload, and non-envelope failures become fixed UI-safe errors. Raw
response bodies, exception details, paths, SQL details, stacks, and credentials
are never surfaced. The client adds no retry, polling, caching, or domain
validation.

## Quality Gate and CI

The frontend check runs, in order:

```text
generated-contract freshness
ESLint
strict TypeScript
Vitest
production Next.js build
```

It is integrated into the existing authoritative repository gate:

```bash
uv run python scripts/check.py
```

The gate assumes `npm --prefix web ci` has already installed dependencies; it
does not install them. The single GitHub Actions quality job now sets up Node 24,
uses the committed lockfile, runs `npm ci`, and then invokes the unified Python
entrypoint. Tests and the production build need no running API or external
network.

Focused coverage verifies loopback origin validation, typed health success and
sanitized failures, request-ID preservation, shell connection and retry states,
future-only navigation, deterministic contract export, and a backend-independent
production build.

## Preserved Boundaries

Sprint 152 adds no:

- S153–S158 business page or placeholder route tree
- paper-job command, domain table, mock financial data, or governance control
- authentication, user, session, token, role, or RBAC behavior
- Docker Compose, container, reverse proxy, or deployment orchestration
- FastAPI CORS change or Next.js BFF domain layer
- Node.js or browser access to SQLite, artifact files, or Python modules
- broker, QMT, MiniQMT, live trading, real-money, or capital behavior
- microservice, Redis, Kafka, distributed queue, or Kubernetes behavior

## Next Sprint

```text
Sprint 153 — Strategy List, Detail, Research, and Backtest Views
```

Sprint 153 may add the first business views while preserving the generated API
contract, same-origin transport, bounded error, navigation, and browser-authority
boundaries established here.
