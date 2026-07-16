# Sprint 160 — Founder Demo Workspace and First-run Experience

## Status

Implementation complete; Founder/CTO product verification and formal Milestone
28 closeout remain separate later actions. Milestone 28 is still **In Progress**.

## Objective

Complete the remaining first-run Product MVP gap without adding quantitative or
execution capability. A new Founder can now choose between a clean standard
workspace with explicit empty-state guidance and an opt-in, isolated,
disposable Demo Workspace with one coherent Strategy-to-Human-Decision journey.

## Delivered Boundary

```text
versioned demo source
  -> validation-only source load
  -> explicit backend/operator installer
  -> isolated artifact roots + SQLite
  -> read-only path-free descriptor API
  -> generated TypeScript contract
  -> descriptor-driven Founder guidance
```

The browser still uses only the fixed same-origin `/api/backend` gateway. It
cannot read demo source files, artifacts, SQLite, Python modules, QMT, or a
broker, and it cannot invoke the installer.

## Versioned Demo Source

`examples/demo_workspace/` contains deterministic, reviewable demo-only inputs:

- the existing registered `moving_average_crossover` strategy identity;
- one research run that validates through existing readers;
- report, strategy-decision, and strategy-review evidence manifests;
- two distinct succeeded paper jobs with attempts and authoritative results;
- ordered comparison candidates;
- a non-executing lifecycle proposal and a deferred human-review input; and
- one optional Paper Job submission example.

IDs and UTC timestamps are fixed. No file contains credentials, secrets,
network dependencies, external downloads, random values, wall-clock values, or
claims of profitability, suitability, approval, live readiness, or future
returns.

## Installer and Storage Authority

`el-psy-quant install-demo-workspace` is an explicit operator command. It:

1. requires workspace mode `demo`;
2. validates the complete source through existing artifact/domain contracts;
3. refuses unrelated non-empty, non-Demo, or conflicting targets;
4. materializes into an isolated staging workspace;
5. upgrades SQLite through Alembic;
6. creates indexes, jobs, attempts, and result references through existing
   repository/application boundaries;
7. keeps completed payloads authoritative in files; and
8. exposes the target only after complete validation succeeds.

Reinstalling the same source version is a validated idempotent replay. Failure
does not expose partial target state. The installer never deletes, migrates,
overwrites, or reinterprets a real user workspace.

## Standard and Demo Startup

Standard startup is unchanged and unseeded:

```powershell
docker compose up --build --detach
```

Demo startup is explicit:

```powershell
docker compose down
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
```

The overlay selects project identity `el-psy-quant-demo`, volume
`el-psy-quant-demo_demo-data`, Demo mode, and Demo-only roots under
`/data/workspace`. It runs the installer before FastAPI serves. It preserves the
same loopback ports and paired Founder authentication, so standard and Demo
instances cannot run simultaneously.

Safe Demo reset addresses only the Demo volume:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down --volumes
```

Returning to standard uses `docker compose up --detach`; the standard
`mvp-data` volume remains untouched by Demo startup and reset.

## Descriptor API

`GET /api/v1/demo-workspace` returns only path-free navigation metadata and
explicit request examples. It includes dataset identity/version, warning,
canonical strategy name, exact research/evidence/job references, ordered
comparison candidates, lifecycle command examples, and the optional Paper Job
submission example.

Research, evidence, paper-result, and lifecycle truth remains behind its
existing authoritative endpoint or domain boundary. Standard mode receives a
bounded `demo_workspace_not_configured` result. The checked-in OpenAPI document
and generated TypeScript types define the Web contract.

## First-run Web Experience

- A healthy empty standard workspace says that the application is running and
  distinguishes empty from unavailable, invalid, or failed sources.
- Demo mode shows a persistent accessible **Demo Workspace** identity and
  disposable-example warning in the shell.
- Overview renders exact guided links supplied by the descriptor.
- Contextual next actions remain choices; generic pages do not connect unrelated
  real-user records or make recommendations.
- Lifecycle example loading fills command inputs but does not submit, approve,
  persist a timeline, or apply a transition.
- Paper Job submission is grouped by run identity, starting account, ending
  account, orders, and fills, with required/optional labels and bounded format
  guidance.
- **Load demo example** fills the form only from the descriptor and never
  submits automatically.

## Preserved Non-goals

Sprint 160 adds no strategy, market data, financial calculation, browser
recomputation, ranking, recommendation, automatic lifecycle transition,
mutable lifecycle current-state field, broker, QMT, MiniQMT, live trading,
capital allocation, background scanner, distributed worker, SaaS behavior,
multi-user system, or broad M29 visual/product refresh.

## Verification Contract

The sprint adds deterministic coverage for source and installed artifacts,
result availability, ordered distinct comparison candidates, installer success
and replay, validation/conflict/refusal paths, atomic failure, storage isolation,
descriptor disabled/enabled behavior, authentication, OpenAPI and generated
contracts, standard first-run states, Demo identity/journey, Strategy guidance,
Lifecycle example loading, and Paper Job form guidance/loading.

The required final verification is:

```text
uv run python scripts/check.py
docker compose config
docker compose -f compose.yaml -f compose.demo.yaml config
```

Docker Demo startup and guided smoke verification are required when Docker is
available. Otherwise, the PR must state that limitation truthfully and report
deterministic installer, API, frontend, OpenAPI, contract, and effective Compose
verification instead.

## Roadmap Handoff

- Sprint 159 is Complete.
- M28 spans S152–S160 and remains In Progress pending Founder/CTO closeout.
- M29 begins only after that closeout.
- M29 retains its hardening intent and is rebased from S160–S165 to S161–S166.
