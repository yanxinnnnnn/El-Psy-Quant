# Founder Web MVP Local Operations

This runbook covers reproducible local startup and verification of the existing
Sprint 152–158 Founder workflows. It is implementation and operating guidance,
not a Milestone 28 governance closeout.

## Runtime Boundary

The local runtime remains one modular application:

```text
Browser
  -> authenticated Next.js Founder workspace
  -> fixed same-origin /api/backend gateway
  -> authenticated FastAPI /api/v1 API
  -> existing application services and domain modules
  -> SQLite operational state and authoritative local artifacts
```

The browser never receives a filesystem path or database connection and never
accesses SQLite, artifact directories, Python modules, QMT, MiniQMT, or a broker.
Compose adds two processes and one local volume; it does not create a
microservice, distributed worker, or competing domain boundary.

## Fresh Checkout Startup

Prerequisites:

- Docker Desktop with Docker Compose v2
- free loopback ports `3000` and `8000`

From the repository root:

```powershell
Copy-Item .env.example .env
```

Edit `.env`. Keep `EL_PSY_QUANT_FOUNDER_USERNAME=founder` or choose another
single local username, and replace the password placeholder with a unique
visible-ASCII password. Do not reuse a system, broker, email, or cloud password.
The file is ignored by Git.

Build and start:

```powershell
docker compose up --build --detach
docker compose ps
```

Wait until `backend` and `web` report `healthy`, then open:

```text
http://127.0.0.1:3000
```

The browser displays an HTTP Basic prompt. Enter the exact values from `.env`.
The workspace and same-origin gateway use the same credential, and the gateway
forwards it to the independently protected versioned FastAPI routes.

Both published ports bind explicitly to `127.0.0.1`. The backend binds to
`0.0.0.0` only inside the private Compose network so the `web` service can reach
the fixed `backend` service name. Next.js accepts that non-loopback destination
only with Compose's explicit `EL_PSY_QUANT_ALLOW_COMPOSE_API_ORIGIN=1` build
setting; direct developer configuration remains loopback-only. FastAPI has no
broad CORS configuration.

## Persistent Local Storage

Compose creates the named `el-psy-quant-mvp_mvp-data` volume and mounts it at
`/data` in the backend container. Backend startup creates the configured roots
and explicitly upgrades the SQLite database before serving traffic:

```text
/data/product.sqlite3  product operational state
/data/research/        authoritative research artifacts
/data/evidence/        authoritative governance/report manifests
/data/paper/           authoritative completed paper outputs
```

An empty research or evidence root produces the existing bounded empty state.
Paper-job list and submission routes are available after the migration reaches
the existing `0005_paper_job_result_references` head. Migrations never run from
the browser or Next.js process.

To copy existing read-only research or evidence artifacts into the running local
volume, preserve their supported layout and use one of these operator commands:

```powershell
docker compose cp C:\path\to\research\. backend:/data/research/
docker compose cp C:\path\to\evidence\. backend:/data/evidence/
```

Restart only the backend if an operating-system permission change requires it;
ordinary artifact reads need no refresh process. Artifact files remain payload
authority. SQLite is not populated with complete artifact payloads.

## End-to-End Smoke Verification

After both services are healthy, run:

```powershell
docker compose exec web node /app/verify-mvp.mjs
```

The verifier uses the container's configured credential without printing it and
checks:

- an unauthenticated gateway request receives a Basic challenge
- authenticated health crosses Next.js and reaches the exact FastAPI contract
- Overview plus every top-level strategy, research, evidence, paper-job,
  portfolio-record, comparison, and lifecycle route returns HTML
- existing strategy, research-run, evidence-manifest, and durable-job reads
  return their checked contracts
- lifecycle proposal and deferred human-review commands normalize successfully
  through the same-origin gateway

The lifecycle commands are synchronous and stateless. Verification does not
submit a durable paper job, create paper outputs, infer approval, apply a
transition, allocate capital, or contact an external system.

For service state and bounded logs:

```powershell
docker compose ps
docker compose logs --tail 100 backend web
```

The health checks send the configured credential but never write it to their
output. Application code must not log `Authorization` or credential environment
variables.

## Normal Stop, Restart, and Reset

Stop processes and preserve all local state:

```powershell
docker compose down
```

Start the same persisted workspace again:

```powershell
docker compose up --detach
```

Changing `.env`, backend settings, or the built Web API destination requires a
recreate; source changes require a rebuild:

```powershell
docker compose up --build --detach --force-recreate
```

`docker compose down --volumes` permanently removes the local product database
and every artifact stored in the named volume. Use it only for an intentionally
disposable environment after confirming those files may be deleted.

## Authentication Contract and Limits

Authentication is deliberately minimal:

- exactly one configured Founder username/password pair
- browser-native HTTP Basic challenge
- constant-time credential comparison at the Web and API boundaries
- no user table, registration, session database, cookie, role, permission graph,
  password reset, OAuth provider, or RBAC
- no TLS termination; safety depends on loopback-only publication

Both variables must be present together or startup/request handling fails
closed. Values use visible ASCII, the username cannot contain `:`, and each
value is limited to 128 characters. Changing the credential requires recreating
both services. Browsers cache Basic credentials for a session, so close all
browser windows for this origin when ending access on a shared machine.

This boundary is appropriate only for the documented Founder-only local machine.
It is not a SaaS or remote-hosting authentication design.

## Direct Developer Workflow

Install dependencies and run the unified gate:

```powershell
uv sync
npm --prefix web ci
uv run python scripts/check.py
```

Create existing local database and artifact directories, configure their paths,
and run the explicit migration. Example:

```powershell
New-Item -ItemType Directory -Force .local\research, .local\evidence, .local\paper
$env:EL_PSY_QUANT_PRODUCT_DATABASE_PATH=(Resolve-Path .local).Path + "\product.sqlite3"
$env:EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT=(Resolve-Path .local\research).Path
$env:EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT=(Resolve-Path .local\evidence).Path
$env:EL_PSY_QUANT_PAPER_ARTIFACT_ROOT=(Resolve-Path .local\paper).Path
$env:EL_PSY_QUANT_FOUNDER_USERNAME="founder"
$env:EL_PSY_QUANT_FOUNDER_PASSWORD="replace-with-a-local-password"
uv run alembic upgrade head
uv run uvicorn el_psy_quant.api.app:app --host 127.0.0.1 --port 8000
```

In a second terminal, configure the same credential and start Next.js:

```powershell
$env:EL_PSY_QUANT_API_ORIGIN="http://127.0.0.1:8000"
$env:EL_PSY_QUANT_FOUNDER_USERNAME="founder"
$env:EL_PSY_QUANT_FOUNDER_PASSWORD="replace-with-a-local-password"
npm --prefix web run dev
```

When both credential variables are absent, the original unauthenticated
developer mode remains available only for a process bound to loopback. Never
bind an unauthenticated API or Web process to a LAN or public interface.

## Troubleshooting

- `docker compose config` reports a missing variable: create `.env` from
  `.env.example` and set both credential values.
- A service stays unhealthy: inspect `docker compose logs --tail 100 backend web`.
- Browser credentials keep failing: confirm both services were recreated after
  editing `.env`, then close and reopen the browser to clear its Basic cache.
- Research or evidence shows an empty state: the configured volume roots are
  valid but contain no supported artifacts; copy an authoritative layout into
  the appropriate root.
- A durable route reports the database unavailable: confirm backend startup
  completed the Alembic upgrade and that the named volume is writable.
- Port binding fails: stop the conflicting local process. Do not change the
  Compose bindings to a non-loopback host for this MVP.
