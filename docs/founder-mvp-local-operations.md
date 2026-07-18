# Founder Web MVP Local Operations

This runbook covers reproducible standard and Demo startup and verification of
the Sprint 152–160 Founder workflows. It is implementation and operating
guidance, not a Milestone 28 governance closeout.

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
Compose adds two processes and one selected local volume; it does not create a
microservice, distributed worker, or competing domain boundary. Standard and
Demo startup select different named volumes and never share product storage by
default.

## Standard Workspace Startup

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

An empty research or evidence root produces explicit first-run guidance rather
than demo records. Standard startup never runs the demo installer and never
seeds product state.
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

## Isolated Demo Workspace Startup

The Demo Workspace is an explicit, disposable alternative to the standard
workspace. Stop the standard instance first because both modes publish the same
loopback ports:

```powershell
docker compose down
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
docker compose -f compose.yaml -f compose.demo.yaml ps
```

The overlay uses Compose project identity `el-psy-quant-demo` and the distinct
`el-psy-quant-demo_demo-data` volume. Before FastAPI serves requests, the
backend validates the complete versioned `examples/demo_workspace/` source,
upgrades only the Demo SQLite database through Alembic, and installs artifacts
and compact records through existing readers, repositories, and services. The
browser cannot invoke the installer.

The install is deterministic and replay-safe for the same dataset version. A
repeat startup validates the existing installation and leaves it unchanged. A
source conflict, invalid source, unrelated non-empty target, or target not
explicitly configured as Demo fails startup without exposing partial installed
state.

Open `http://127.0.0.1:3000` with the same `.env` Founder credential. The shell
shows a persistent **Demo Workspace** identity and warns that records are
disposable examples, not real user evidence. From Overview, follow the exact
backend-provided journey:

```text
Strategy -> Research Evidence -> Governance Evidence -> Paper Run
  -> Portfolio Result -> Comparison -> Lifecycle Review
  -> Human Decision Evidence
```

The lifecycle example remains non-executing. Its deferred human-review input is
governance evidence and does not create mutable current state. The optional
Paper Job example only fills the form after an explicit user action; it never
submits automatically.

Stop while preserving the installed Demo Workspace:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down
```

Reset only disposable Demo storage, then reinstall:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down --volumes
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
```

This reset does not address the standard `mvp-data` volume. To return to the
standard workspace, stop Demo and run `docker compose up --detach`. Never run
the standard `docker compose down --volumes` command unless the real local
database and authoritative artifacts may be deleted.

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
- standard mode returns the bounded Demo-not-configured response; Demo mode
  follows descriptor-provided strategy, research, evidence, job, result,
  comparison, proposal, and deferred-review references

The lifecycle commands are synchronous and stateless. Verification does not
submit a durable paper job, create paper outputs, infer approval, apply a
transition, allocate capital, or contact an external system.

## Bilingual Browser Acceptance

Sprint 162 deterministic checks do not replace Founder runtime acceptance. In
both Standard and Demo modes, verify:

- the header switcher exposes **English** and **简体中文** and survives reload;
- `<html lang>` and document metadata follow the active language;
- the current unprefixed route is unchanged after switching;
- repeated ordered comparison `job_id` parameters remain in exact order;
- representative navigation, forms, confirmations, loading/empty/error states,
  Demo identity, and the complete guided journey are translated;
- in-progress Paper Job and Lifecycle form fields remain populated;
- raw IDs, states, error codes, UTC timestamps, quantitative values, artifact
  text, ordering, and duplicates remain unchanged; and
- switching language never submits or chains a command.

The `el_psy_quant_locale` cookie is a local display preference shared by
Standard and Demo because both use the same loopback origin. If an unsupported
or malformed value is present, the application falls back to English. Clearing
site data resets the preference but also clears any other browser state for that
origin; it does not alter SQLite or artifact storage.

## Sprint 163 Rendered Visual Acceptance

Sprint 163 deterministic tests do not replace Founder browser review. With the
Standard and Demo workspaces started through their documented isolated Compose
flows, verify both `English` and `简体中文` at approximately `360px`, `768px`, and
`1280px+`:

- visit Overview and every existing Strategy, Research, Evidence, Paper Job,
  Portfolio Record, Comparison, and Lifecycle list/detail/form route;
- confirm the workspace header, current navigation, language switcher, and
  Standard/Paper identity remain visible and keyboard-operable;
- confirm Demo mode shows the persistent localized Demo label and disposable
  example-data warning on every route;
- exercise available loading, empty, invalid, unavailable, error, conflict,
  pending, success, and partial-failure surfaces;
- inspect long IDs, artifact keys, raw UTC timestamps, schemas, code, ordered
  duplicate records, tables, and backend-detail disclosures;
- confirm tables and tablet navigation scroll within their own containers and
  the page itself has no horizontal overflow;
- confirm text-bearing controls, Chinese headings, labels, badges, warnings,
  and repeatable form rows wrap without clipping;
- use keyboard-only navigation and inspect visible focus, named landmarks,
  captions, labels, alerts, and disclosures;
- enable reduced-motion preference and confirm no essential information depends
  on animation; and
- switch language with repeated comparison parameters and unsaved Paper Job and
  Lifecycle fields present, confirming no route, query, value, or command
  regression.

Rendered acceptance is visual and behavioral review only. It must not interpret
operational completion as profitability, human approval as execution, or a
lifecycle proposal as an applied transition. Record acceptance before merging
Sprint 163 or starting Sprint 164.

The exact token and component contract is documented in
`docs/product/visual-system.md`.

## Sprint 164 Founder Dashboard Acceptance

Sprint 164 deterministic tests do not replace Founder browser review. In
Standard and Demo, verify `English` and `简体中文` at approximately `360px`,
`768px`, and `1280px+`:

- confirm Dashboard identity agrees with the persistent shell identity and Demo
  shows descriptor-owned identity plus the disposable-example warning;
- confirm process health is described as process health only and failed
  research, evidence, or product-database reads produce partial/unavailable
  readiness rather than aggregate health;
- exercise healthy-empty, populated, unavailable, invalid, and partial states,
  keeping raw error code, sanitized detail, request ID, localized guidance, and
  an individual retry action;
- confirm one failed region does not erase independent successful regions and
  explicit refresh does not poll or send a command;
- inspect the bounded Paper Job list for exact backend order, duplicates, job/run
  IDs, localized plus raw job and attempt status, submitted/updated UTC values,
  and exact job/result links;
- confirm queued, failed, running/interrupted, result-available,
  healthy-no-evidence, and dependency-failure attention conditions are
  operational only;
- select result candidates in a deliberate non-source order, including a
  duplicate if present, and confirm the Comparison URL repeats `job_id` in the
  exact selection order;
- confirm no result is auto-selected, ranked, scored, recommended, called a
  winner, or financially recalculated;
- confirm research and evidence remain separate source-ordered regions and no
  unified chronology is implied;
- confirm Standard workflow choices are generic while every Demo journey link
  and raw identity comes from the descriptor;
- confirm no Run, Retry, Recover, Cancel, submission, lifecycle proposal, or
  human-review command is available from Dashboard cards;
- use keyboard-only navigation to operate region links, disclosures, named read
  retries, comparison checkboxes, and visible focus; and
- confirm long English/Chinese copy, IDs, badges, cards, and controls wrap
  without global horizontal page overflow.

There is no durable lifecycle GET/list/current-state contract, so Dashboard must
not claim a persistent pending lifecycle review. Record local Dashboard
acceptance before merging Sprint 164 or beginning Sprint 165.

## Sprint 165 Paper Job Reliability Acceptance

Sprint 165 deterministic checks do not replace Founder Standard/Demo runtime
acceptance. In both workspaces and both locales, verify:

- a first keyed submission displays **Created**, keeps the completed form and
  exact key, shows raw/localized `queued`, and never calls Run;
- an exact replay displays **Exact replay**, links the original current job in
  any durable status, and creates no second job, attempt, output, or reference;
- reusing the same key with a different canonical request preserves every form
  value and explains the bounded idempotency conflict without claiming a
  field-level diff or generating a replacement key;
- a confirmed Run returns a `running` representation with one attempt number,
  attempt ID, and raw status before completion, explains the non-durable
  post-response limitation, and requires manual refresh with no polling;
- duplicate Run and Run/Cancel races produce one transition winner while the
  loser receives the stable state conflict and refresh guidance;
- Retry is visible only for `failed`, performs no execution, creates no attempt,
  and returns the job to `queued` only when outputs and compact references are
  absent;
- Recover is visible only for `running`, shows the loaded raw
  `updated_timestamp`, rejects non-UTC and earlier thresholds before sending,
  and requires an explicit Founder assertion that execution is stale;
- each recovery outcome (`requeued`, `succeeded`, `failed`) is presented
  explicitly, while uncertain inspection leaves the job running;
- output/reference conflicts preserve the last settled job, attempts, raw code,
  request ID, and all existing files without overwrite, cleanup, or automatic
  follow-on command;
- keyboard confirmation, pending disabled controls, alerts/status messages,
  associated recovery field errors, visible focus, long IDs/copy, and wrapping
  work at approximately `360px`, `768px`, and `1280px+`; and
- switching `English`/`简体中文` preserves in-progress submission and recovery
  input without changing raw statuses, codes, IDs, timestamps, or issuing a
  command.

The callback after Run is not a durable worker and does not provide
exactly-once execution. If the process exits after claim, the durable job and
attempt remain `running` for an explicit Recover decision. Migration head
remains `0005_paper_job_result_references`; Sprint 165 adds no migration,
worker, lease, heartbeat, scheduler, polling, or cleanup behavior.

Founder local Standard/Demo reliability acceptance and the Sprint 165 merge are
complete.

## Sprint 166 Error and Observability Acceptance

Sprint 166 deterministic checks do not replace Founder runtime acceptance. In
isolated Standard and Demo workspaces, both locales, and representative
`360px`, `768px`, and `1280px+` widths:

- exercise a valid empty source, exact not-found entity, invalid input or
  artifact, unavailable local dependency, state/output conflict, and sanitized
  unexpected failure;
- confirm each surface keeps localized category, explanation, and safe recovery
  beside the raw operation, HTTP status, entity ID, stable code, server request
  ID, and bounded backend detail;
- confirm the Web never invents a missing request ID and unknown future codes
  preserve their raw value with generic guidance;
- inspect all six Paper Job attempt codes in English and Simplified Chinese and
  verify Interrupted does not claim work never started, while partial/invalid
  output guidance never authorizes cleanup or overwrite;
- correlate the exact request ID across one request completion, one successful
  Paper Job command, and Run completed, expected-failed, or uncertain events;
- confirm expected execution failure uses the persisted approved attempt code
  and uncertain execution uses only `internal_execution_failure`;
- confirm product events contain no credentials, headers, cookies, query
  strings, bodies, idempotency keys, paths, SQL, exception text, tracebacks,
  financial values, or artifact payloads;
- confirm empty, unavailable, invalid, not found, and conflict remain distinct,
  and that Refresh, Retry, and Recover remain separate explicit actions;
- confirm long raw values wrap, disclosures are keyboard accessible, and
  localized guidance does not alter authoritative values; and
- confirm Standard and Demo databases and artifact roots remain isolated.

Use [the focused error and observability runbook](operations/error-observability-and-audit.md)
for the troubleshooting matrix, event fields, denylist, transient/durable
evidence distinction, and current limitations.

Record Founder local Standard/Demo error-surface and observability acceptance
before merging Sprint 166 or beginning Sprint 167.

For service state and bounded logs:

```powershell
docker compose ps
docker compose logs --tail 100 backend web
```

The health checks send the configured credential but never write it to their
output. Application code must not log `Authorization` or credential environment
variables.

## Standard Stop, Restart, and Reset

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

For a direct developer Demo installation, use a dedicated empty directory and
set Demo mode explicitly. Do not point these variables at standard or real-user
storage:

```powershell
New-Item -ItemType Directory -Force .local-demo
$demoRoot=(Resolve-Path .local-demo).Path
$env:EL_PSY_QUANT_WORKSPACE_MODE="demo"
$env:EL_PSY_QUANT_DEMO_WORKSPACE_ROOT=$demoRoot
$env:EL_PSY_QUANT_PRODUCT_DATABASE_PATH="$demoRoot\product.sqlite3"
$env:EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT="$demoRoot\research"
$env:EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT="$demoRoot\evidence"
$env:EL_PSY_QUANT_PAPER_ARTIFACT_ROOT="$demoRoot\paper"
uv run el-psy-quant install-demo-workspace --source-root examples/demo_workspace --workspace-root $demoRoot --alembic-config alembic.ini
```

The command performs its own Alembic upgrade. Repeating it with the same source
is a validated replay. Use a different empty directory to test another source
version; the installer will not overwrite a conflicting or unrelated target.

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
- The Demo service exits before serving: inspect backend logs for a bounded
  source-validation, dataset-conflict, or non-empty-target refusal. Do not move
  or copy real files into the Demo volume to work around the refusal.
- Demo and standard cannot start together: this is expected because both use
  `127.0.0.1:3000` and `127.0.0.1:8000`; stop one mode before starting the other.
