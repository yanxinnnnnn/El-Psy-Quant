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
| S198 | Strategy Runtime Reference and Signal Contract Foundation | In Progress |
| S199 | Deterministic Strategy Signal Evaluation Foundation | Planned |
| S200 | Account-Bound Order Intent and Idempotency Foundation | Planned |
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
