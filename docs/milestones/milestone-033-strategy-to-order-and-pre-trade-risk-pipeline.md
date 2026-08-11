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
| S200 | Account-Bound Order Intent and Idempotency Foundation | Complete |
| S201 | Pre-Trade Risk Decision and Evidence Foundation | Complete |
| S202 | Durable M33 Persistence, Migration, Concurrency, and Application Service | Complete |
| S203 | Versioned Strategy-to-Risk API, Errors, Audit, and Generated Contracts | Complete |
| S204 | Bilingual Founder Strategy-to-Risk Workspace | In Progress |
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
progression, execution, fill, or account mutation.

## Sprint 201 Result

Sprint 201 adds the pure deterministic pre-trade risk boundary:

- one immutable `long_only_cash_risk_v1` policy reference with optional exact
  maximum quantity and notional;
- one immutable risk command bound only to a complete S200 intent and policy;
- exact `latest_trade_price_v1` evidence from the consumed M32 prefix;
- exact requested-quantity-times-price notional without rounding;
- four always-present ordered position, quantity, notional, and cash rules;
- deterministic `risk_input_<digest>` snapshot identity; and
- immutable `risk_decision_<digest>` allow/reject evidence with stable ordered
  reasons and cryptographically revalidated command provenance.

Evaluation recreates exact intent, account, calendar, session, replay, cursor,
current-event, and policy anchors. Changed authority fails stale. Missing,
invalid, tampered, unsupported, or unrepresentable input fails closed without a
decision and never defaults to allow. Lifecycle-only replay status changes do
not change market identity when the exact stream and cursor prefix remain
unchanged.

The price reference is risk evidence only, and a decision is not a reservation,
execution authorization, fill, valuation, ledger posting, or account/replay
mutation. Sprint 201 adds no persistence, migration, application service, API,
Web, Demo, worker, scheduler, broker, or execution behavior.

## Sprint 202 Result

Sprint 202 adds the durable M33 product boundary:

- additive migration `0010_strategy_order_risk` with immutable Signal, Intent,
  Decision, and command-receipt tables;
- canonical full-payload authority plus unique deterministic identities,
  digests, foreign references, indexes, and append-only triggers;
- strict reconstruction that rejects duplicate-key, non-canonical, malformed,
  incomplete, digest-mismatched, and cross-reference-mismatched rows;
- bounded identity/digest/filter repositories without unbounded reads or repair;
- one-winner `BEGIN IMMEDIATE` transactions and scoped durable idempotency;
- exact no-action replay through receipts without manufacturing an Intent row;
  and
- thin application services that reopen and verify exact M31/M32 authority
  before invoking the unchanged S198–S201 pure functions.

Sprint 202 adds no API, OpenAPI, generated TypeScript, Web, Demo, worker,
reservation, execution, fill, replay progression, or ledger/account mutation.

## Sprint 203 Result

Sprint 203 adds exactly nine authenticated versioned operations over the S202
application boundary. Strict public requests accept only approved selections,
references, expected authority anchors, actors, and idempotency keys. Complete
inspection responses preserve canonical decimal strings and raw authority
values while omitting command idempotency keys and raw event payloads.

List reads are bounded to 1–200 records and use deterministic collection-bound
opaque keyset cursors. Central sanitized translation exposes stable not-found,
conflict, invalid-input, schema, authority, busy, and storage errors through the
existing request-ID envelope. Successful commands emit bounded correlation
events without actors, keys, financial values, payloads, SQL, or paths.
Canonical OpenAPI and generated TypeScript now include the nine stable
operation IDs and strict unions.

Sprint 203 adds no Web workflow, Demo, migration, worker, reservation,
execution, fill, replay progression, or ledger/account mutation.

## Sprint 204 Result

Sprint 204 adds one bilingual `/strategy-to-risk` Founder workspace over the
checked-in generated S203 contracts. It loads exact M31 Paper Account and M32
calendar/session/replay anchors, preserves them until explicit refresh or
reselection, and provides three explicit commands for Signal evaluation, Intent
or no-action derivation, and pre-trade Risk evaluation.

Fail-closed validators require complete nested runtime, market, account, Intent,
policy, price, and Decision references plus exactly four ordered risk-rule
records. New versus replayed evidence, valid allow versus reject, no-action,
stale authority, reconciliation, invalid configuration, unavailable authority,
storage failure, and sanitized unexpected failures remain distinct. Raw IDs,
digests, codes, canonical decimals, and timestamps remain unchanged across
locales.

Sprint 204 adds no domain, persistence, API, OpenAPI, generated-contract, Demo,
migration, worker, reservation, Paper Account/replay mutation, execution order,
fill, broker, or live behavior. S204 remains the current implementation sprint
until Founder merge/acceptance; S205–S206 remain Planned, and the migration head
is `0010_strategy_order_risk`.

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
