# Sprint 167 — Migration, Test, and Local Deployment Hardening

## Status

Implementation complete; Founder migration and local deployment acceptance
remains. Milestone 29 remains **In Progress**.

Sprint 168 — Milestone 29 Closeout and M30 Handoff becomes next only after this
implementation is merged and the Founder completes the Standard/Demo
migration/deployment acceptance matrix.

## Objective

Make fresh installation, existing-volume upgrade, startup refusal, read-only
verification, Demo replay/reset, return to Standard, and dependency
reinstallation explicit and reproducible without changing product behavior or
durable schema.

## Delivered Contract

```text
reviewed locked inputs
  -> exact Standard or Demo Compose identity
  -> forward migration or validated Demo install/replay
  -> read-only workspace verification
  -> Uvicorn
  -> authenticated bilingual non-mutating smoke
```

The migration head remains `0005_paper_job_result_references`. One application
constant is checked against Alembic's single linear head and is shared by API
preflight, Demo validation, and local verification. No migration file or schema
was added or changed.

## Migration and Verification Hardening

Deterministic temporary-SQLite coverage now proves:

- exact direct ancestry from `0001` through `0005`, with one head and no branch
  or merge revision;
- `base`, `0001`, `0002`, `0003`, and `0004` independently upgrade to head;
- representative historical rows survive unchanged;
- an already-current populated database and authoritative artifact file remain
  unchanged on repeat upgrade;
- the exact final tables, columns, constraints, foreign keys, and index shape;
- offline generation creates no database and configuration is independent of
  the process working directory; and
- missing, malformed, incompatible, older, newer, empty, or multi-row revision
  state fails read-only preflight without reset.

`el-psy-quant verify-local-workspace` accepts explicit `--mode` and
`--workspace-root`. Standard verification checks the real root, database,
current schema, exact API-used tables/columns, contained artifact roots, and
absence of Demo identity. Demo verification checks the exact installed layout,
marker/descriptor agreement, current schema, and descriptor-owned research,
evidence, Paper Job/result, comparison, proposal, and review boundaries.
Verification creates nothing, runs no migration/installer, executes no product
command, and makes no network request.

## Startup and Isolation

The focused `start-local-backend` entrypoint enforces:

```text
Standard: fixed roots -> upgrade -> Standard verify -> Uvicorn
Demo: validate/install or exact replay -> upgrade -> Demo verify -> Uvicorn
```

Any preparation, migration, installation, or verification failure prevents
Uvicorn. Standard never configures a Demo source/root and receives no reset
path. Demo refuses unrelated, mismatched, or Standard targets. Static tests
preserve the exact project, volume, mount, loopback port, authentication,
backend-origin, and healthcheck contracts.

## Locked Build and Smoke Inputs

`uv.lock` remains development/CI authority. CI uses `uv sync --locked`, checks
the lock, and checks the committed exact `requirements-runtime.txt` export.
The backend image installs that runtime export before installing the local
project with `--no-deps`; the final runtime input excludes dev dependencies.
The Web remains on `npm ci` and `package-lock.json`.

Cold builds still require uncached base images and package artifacts, and
floating upstream image tags remain an external risk. No proxy or new package
manager was added.

The Web verifier now uses only authenticated reads plus the existing
locale-preference endpoint. It checks both document languages and representative
copy, route preservation, raw identity stability, Standard valid-empty and
Demo descriptor behavior, request IDs, and sanitized errors. It issues no Paper
Job or lifecycle command and prints no response body, credential, or private
header on failure.

## Operations and Recovery Guidance

`docs/operations/local-install-upgrade-and-recovery.md` consolidates:

- fresh Standard and Demo startup;
- cold full-`/data` backup before a Standard upgrade;
- source commit and migration-revision recording;
- post-upgrade read-only verification;
- exact Demo replay, Demo-only reset, and return to Standard;
- complete backup-set and stopped-SQLite requirements;
- restore-to-new-empty-target-first guidance; and
- the absence of automatic backup, restore, repair, downgrade, or destructive
  Standard reset.

Demo should normally be reinstalled. Raw local copies are not claimed to be
production disaster recovery, and external backup security remains the
Founder's responsibility.

## Preserved Boundaries

Sprint 167 adds no migration, schema, domain behavior, Paper Job semantic, API
contract, financial calculation, lifecycle behavior, worker, queue, scheduler,
polling, broker/QMT behavior, cloud deployment, proxy configuration, durable
deployment record, backup registry, or Standard volume-reset helper.

## Verification and Founder Handoff

Codex must run:

```text
uv run python scripts/check.py
docker compose config
docker compose -f compose.yaml -f compose.demo.yaml config
```

Only the last two non-starting static Compose commands are permitted. Docker
build/start/stop, image pulls, container health/smoke, volume removal, and
runtime acceptance remain Founder-owned under project policy.

Founder acceptance covers cold backup, fresh Standard, existing prior-revision
upgrade, repeat-at-head preservation, migration refusal, fresh/exact Demo,
Demo-only reset, return to Standard, both locales, container health/smoke, and
browser behavior before merge.

Final Codex verification:

- `uv run python scripts/check.py` passed;
- Python: 2,187 passed and 3 skipped;
- Ruff, package import, CLI help, lock/export parity, message catalogs,
  OpenAPI/generated contracts, ESLint, and TypeScript passed;
- Web: 36 test files and 316 tests passed;
- the Next.js production build completed all 12 page-data entries;
- `docker compose config` passed with temporary non-secret environment values;
- `docker compose -f compose.yaml -f compose.demo.yaml config` passed with
  temporary non-secret environment values; and
- Docker build, image pull, container startup, runtime smoke, stack stop, and
  volume removal were intentionally not attempted under project policy.
