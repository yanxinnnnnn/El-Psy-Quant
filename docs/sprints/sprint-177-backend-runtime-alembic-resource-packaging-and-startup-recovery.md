# Sprint 177 — Backend Runtime Alembic Resource Packaging and Startup Recovery

## Status

**Implementation complete; Founder preserved-volume recovery and complete
Standard/Demo runtime acceptance remain pending.**

Milestone 30 remains In Progress. Sprint 178 — Milestone 30 Closeout and M31
Handoff remains blocked until Sprint 177 is merged and Founder runtime acceptance
succeeds.

## Reproduced Founder failure and root cause

Founder Standard startup used the preserved `mvp-data` volume and failed before
serving because the runtime-only backend image installed the project wheel while
`/app/alembic.ini` resolved migrations under `/app/src`. The final image correctly
contained no repository `src/` tree, so Alembic could not find its script
directory.

Founder diagnosis retained a cold copy of the complete stopped `/data` tree and
proved the SQLite database was healthy at exact revision
`0005_paper_job_result_references`, with expected 0005 tables and no
`portfolio_reviews` table. That copied database upgraded to 0006 from the source
checkout. Runtime UID/GID ownership and write permissions were also valid. The
blocker was therefore packaged migration-resource resolution, not corruption,
schema drift, partial migration, volume ownership, or Standard/Demo identity.

## Delivered boundary

Alembic now uses its installed-package resource syntax to resolve the one
authoritative tree under
`el_psy_quant/persistence/migrations`. The same configuration works in the
development checkout, an installed wheel outside the repository, and the
wheel/runtime-only backend image. Startup preflights the exact required resource
files, exact approved linear chain, and single `0006_portfolio_reviews` head
before Standard preparation, Demo installation, database migration, or serving.
Known resource failures expose only a stable bounded identity.

The final backend stage remains limited to exact locked runtime requirements,
the built project wheel, `alembic.ini`, Demo source, and the healthcheck. It does
not install build tooling, use an editable project, copy the repository or full
`src/` tree, mount source, or depend on `/app/src`.

No migration file, revision ID, revision order, product schema, domain
calculation, API contract, Web behavior, Demo data, volume identity, proxy
configuration, or M31+ behavior changed.

## Deterministic packaged-wheel regression

`scripts/check_packaged_migration_resources.py` runs through the repository gate
and:

- builds the wheel offline with locked Hatchling and build isolation disabled;
- verifies each approved migration resource occurs exactly once in the wheel;
- installs the wheel into a temporary location outside the repository source;
- proves imports and direct Alembic resolve that installed copy;
- proves the exact single `0006_portfolio_reviews` head;
- upgrades a fresh database to head;
- upgrades a populated exact-0005 database to 0006 while preserving all existing
  tables and data and adding the approved `portfolio_reviews` schema; and
- removes a required file and injects a mismatched head in temporary installed
  copies to prove resource preflight fails before database creation.

Focused tests also prove Standard artifacts remain unchanged, no Standard
preparation occurs, no Demo installer runs, Uvicorn is never called, output is
bounded, and the Dockerfile cannot regress to a full-source runtime design.

## Founder-owned recovery acceptance

Keep the existing cold backup and preserved Standard volume. Do not remove or
replace the volume, edit or stamp the database, downgrade, or selectively restore
files. After merge, rebuild the reviewed backend image, start against that same
volume, and confirm the supported 0005-to-0006 upgrade followed by read-only
Standard verification and bilingual MVP smoke. Then complete Demo v2 reset and
installation, replay, decision persistence, return-to-Standard, isolation, and
bilingual browser acceptance.

Codex does not build or pull images, start containers, run container smoke,
mutate volumes, reset Demo, or perform browser acceptance. Founder acceptance
and the merge decision remain pending.
