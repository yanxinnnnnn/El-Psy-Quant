# Milestone 33 — Strategy-to-Order and Pre-Trade Risk Pipeline

## Status

**In Progress** through Sprints 197–206.

Issue #389 is the authoritative M33 architecture and planning source. Each
implementation sprint remains governed by its own Issue body.

## Goal

Establish a deterministic, durable, auditable path from one exact versioned
strategy runtime and M32 replay prefix to:

```text
Strategy Signal
  -> M31-account-bound Order Intent or no-action result
  -> immutable allow/reject Pre-Trade Risk Decision
  -> future M34 execution candidate
```

M33 must reproduce the same identities, digests, outcomes, and reason codes from
the same exact strategy, configuration, account head, market prefix, and risk
policy across restart.

## Authority Model

M33 introduces exactly three new authorities:

1. Strategy Signal recommendation evidence.
2. Account-bound, risk-pending Order Intent authority.
3. Immutable Pre-Trade Risk Decision evidence.

A signal is not an order. An intent is not execution. An allow decision is not
a fill or ledger mutation. Persistence, API, Web, Demo, and logs cannot replace
domain authority.

M31 financial/account authority and M32 market-time/replay authority remain
frozen and separate.

## Approved Sprint Sequence

| Sprint | Deliverable | Status |
|---:|---|---|
| S197 | Milestone 33 Architecture and Planning | Complete |
| S198 | Strategy Runtime Reference and Signal Contract Foundation | Complete |
| S199 | Deterministic Strategy Signal Evaluation Foundation | Complete |
| S200 | Account-Bound Order Intent and Idempotency Foundation | In Progress |
| S201 | Pre-Trade Risk Decision and Evidence Foundation | Planned |
| S202 | Durable M33 Persistence, Migration, Concurrency, and Application Service | Planned |
| S203 | Versioned Strategy-to-Risk API, Errors, Audit, and Generated Contracts | Planned |
| S204 | Bilingual Founder Strategy-to-Risk Workspace | Planned |
| S205 | Demo v5, Integration, Upgrade, Restart, Recovery, and Acceptance Hardening | Planned |
| S206 | Milestone 33 Closeout and M34 Handoff | Planned |

## Sprint 198 Result

Sprint 198 adds the pure `el_psy_quant.strategy_order` contract package:

- one closed v1 moving-average runtime reference;
- one trusted exact M32 signal-market reference;
- one pure signal-evaluation command;
- one immutable deterministic Strategy Signal;
- one compact trusted Strategy Signal reference; and
- canonical JSON, digest, UTC timestamp, and M31 quantity boundaries.

Sprint 198 does not evaluate a strategy or interpret market payloads. It adds no
Order Intent, no-action result, risk policy, persistence, migration, application
service, API, Web, localization, Demo, account mutation, replay progression, or
execution behavior. The migration head remains `0009_market_time_runtime`.

## Sprint 199 Result

Sprint 199 adds the first pure deterministic evaluation path:

- one explicit `StrategySignalRuntimeAdapter` boundary;
- exact closed resolution of `moving_average_crossover / v1 / v1`;
- reconstruction and exact matching of concrete M32 calendar, session, replay,
  stream, cursor, current-event, time, and instrument authority;
- selection of only finite positive same-instrument trade prices from the exact
  consumed prefix in M32 order;
- a strict `slow_window + 1` minimum history rule;
- reuse and strict output validation of the existing research Strategy seam;
- exact long-only position-to-target mapping; and
- immutable Sprint 198 Signal construction with deterministic identity.

Pandas inputs and research results remain ephemeral. Sprint 199 adds no account
read, Order Intent, risk, persistence, migration, API, Web, Demo, replay
progression, execution, fill, or account mutation.

## Sprint 200 Result

Sprint 200 adds the pure deterministic account-bound conversion boundary:

- one narrow validator exposing complete M31 ledger-state validation;
- one immutable account reference copied from exact active M31 state and bound
  to the Signal instrument;
- one immutable Signal/account/policy/idempotency command;
- exact target-versus-current buy/sell/no-action conversion;
- deterministic `oi_<digest>` Order Intent identity;
- deterministic `no_action_<digest>` target-satisfied evidence;
- one compact trusted intent reference; and
- the closed proposed/risk-allowed/risk-rejected future lifecycle vocabulary.

Every Signal and account anchor is recreated at conversion. Changed account
head, event, chain, cash, available cash, position, lifecycle, or Signal fails
stale. Different command keys, actors, command digests, and audit timestamps
over identical authority converge on the same intent or no-action identity.

M31 ledger replay remains account-state authority; the S200 reference is copied
evidence only. No-action is not executable intent evidence. Sprint 200 adds no
risk evaluation, persistence, reservation, migration, API, Web, Demo, replay
progression, execution, fill, or account mutation. S201–S206 remain Planned,
and the migration head remains `0009_market_time_runtime`.

## Exit Criteria

M33 is Complete only when:

- one exact runtime and replay prefix produce a deterministic signal;
- one exact M31 account head produces a deterministic intent or no-action result;
- one exact risk snapshot produces a deterministic allow/reject decision;
- retries, concurrency, persistence, and recovery preserve exact authority;
- API, Web, and Demo expose rather than calculate authority;
- stale account and replay anchors fail closed; and
- no M34 execution, fill, or account-mutation behavior is pre-implemented.

M34 remains the first execution/fill/account-mutation milestone.
