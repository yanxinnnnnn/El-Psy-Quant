# Milestone 33 Closeout — Strategy-to-Order and Pre-Trade Risk Pipeline

## Status

Milestone 33 is Complete after Sprint 206 closeout merge.

Issue #389 remains the authoritative M33 architecture source for the delivered
boundary. Sprint 206 records the final repository closeout and the handoff to
Milestone 34 without changing runtime behavior.

## Delivered Capability

M33 delivered one deterministic, durable, auditable strategy-to-risk chain over
frozen M31 Paper Account and M32 market-time authority:

```text
M31 durable Paper Account authority
  + M32 durable calendar/session/event/replay authority
  -> immutable StrategySignal recommendation evidence
  -> immutable account-bound M33 OrderIntent or deterministic no-action
  -> immutable PreTradeRiskDecision allow/reject evidence
  -> future M34 execution candidate only
```

The same exact runtime configuration, account head, replay prefix, session,
instrument, and risk policy reproduce the same Signal, Intent/no-action,
Decision identities, digests, outcomes, and reason codes across restart.

## Completed Sprint Chain

| Sprint | Delivered boundary | Status |
|---:|---|---|
| S197 | Milestone 33 Architecture and Planning | Complete |
| S198 | Strategy Runtime Reference and Signal Contract Foundation | Complete |
| S199 | Deterministic Strategy Signal Evaluation Foundation | Complete |
| S200 | Account-Bound Order Intent and Idempotency Foundation | Complete |
| S201 | Pre-Trade Risk Decision and Evidence Foundation | Complete |
| S202 | Durable M33 Persistence, Migration, Concurrency, and Application Service | Complete |
| S203 | Versioned Strategy-to-Risk API, Errors, Audit, and Generated Contracts | Complete |
| S204 | Bilingual Founder Strategy-to-Risk Workspace | Complete |
| S205 | Demo v5, Integration, Upgrade, Restart, Recovery, and Acceptance Hardening | Complete |
| S206 | Milestone 33 Closeout and M34 Handoff | Complete after merge |

## Final Authority Model

### StrategySignal

A StrategySignal is immutable evidence that one exact versioned strategy runtime
evaluation recommended one exact target from one exact M32 replay prefix.
Recommendation status remains advisory.

Signal authority owns no account mutation, risk decision, execution order, fill,
reservation, or ledger event. Its deterministic identity, digest, runtime
reference, and market binding remain exactly as delivered by S198–S202.

### M33 OrderIntent

An M33 OrderIntent is one immutable account-bound, risk-pending requested trade
delta derived from one exact Signal and one exact verified M31 account head.
Side and requested quantity are domain-derived. Callers and the Web never author
them as authority.

A target already satisfied by the exact account state produces deterministic
no-action evidence and no executable Intent row. An Intent is not an accepted,
routed, executed, partially filled, filled, cancelled, reserved, or ledger-
posting order.

### PreTradeRiskDecision

A PreTradeRiskDecision is immutable `allow` or `reject` evidence over one exact
Intent plus exact account, market, price-policy, and risk-policy input snapshot.
The decision preserves the ordered four-rule evidence and stable reject reason
codes.

An `allow` result is not automatically fresh execution authorization. A reject
does not mutate or cancel the Signal or Intent. M33 never reserves cash or
positions and never posts to the M31 ledger.

### Preserved upstream authority

M31 remains unchanged:

```text
immutable ledger events/postings = financial authority
deterministic ledger replay = Paper Account state authority
projection/snapshot/reconciliation = derived evidence/cache
```

M32 remains unchanged:

```text
TradingCalendar / TradingSession = calendar/session authority
MarketDataEvent = canonical market-state event authority
MarketDataReplayEngine = ordering, cursor, lifecycle, and progression authority
```

M33 consumes exact verified M31/M32 anchors and does not redefine or mutate
either authority.

## Persistence and Migration

Sprint 202 added the single M33 migration:

```text
0009_market_time_runtime
  -> 0010_strategy_order_risk
```

The final migration head for M33 is exactly:

```text
0010_strategy_order_risk
```

Durable Signal, Intent, Decision, and scoped command-receipt rows are append-only
and strictly reconstructed from canonical payloads. Unique deterministic
identities/digests, restrictive references, and one-winner SQLite transactions
provide restart-safe idempotency and concurrency without introducing a second
authority source.

No migration `0011` belongs to M33.

## API, Web, and Demo Surfaces

Sprint 203 exposes exactly nine authenticated versioned M33 product operations:
create/list/detail for Strategy Signals, Order Intents, and Pre-Trade Risk
Decisions, with Signal creation represented as evaluation. No-action remains a
command result rather than a list/detail resource.

Canonical OpenAPI and generated TypeScript are transport contracts only. Stable
errors, request IDs, bounded audit events, and opaque keyset pagination expose
and correlate authority without calculating it.

Sprint 204 adds one bilingual `/strategy-to-risk` Founder workspace using only
the generated S203 transport contracts. It explicitly orchestrates Signal ->
Intent/no-action -> Risk and preserves raw IDs, digests, codes, canonical decimal
strings, timestamps, stale anchors, and replay semantics. The browser does not
calculate Signal targets, side, quantity, reference price, notional, or risk
outcome.

Sprint 205 extends the isolated Demo system to descriptor/dataset v5. Demo v5
generates M33 authority only through the merged S202 application/domain/
repository path; it does not direct-seed Signal, Intent, Decision, or receipt
rows. Descriptor metadata remains non-authoritative discovery and verification
metadata.

Standard remains unseeded and persistent. Demo remains isolated and disposable.

## Idempotency, Concurrency, Restart, and Recovery Evidence

The merged S202–S205 implementation proves:

- exact command retry returns the same verified authority with replay semantics;
- same idempotency key with changed command content conflicts;
- alternate keys may converge on the same deterministic authority while keeping
  valid scoped receipts where the contract permits it;
- duplicate creation races have exactly one durable authority winner;
- restart/reopen preserves Signal, Intent/no-action, Decision, receipt mapping,
  IDs, digests, and bounded read results;
- stale M31 account anchors and stale M32 replay anchors fail closed without
  partial authority or receipt writes;
- representative persisted authority/receipt corruption fails closed and is not
  silently repaired or recomputed from current authority;
- populated `0009 -> 0010` upgrades preserve existing M31/M32 authority; and
- explicit Demo v5 install/read-only verification remains separate from
  migration-time behavior.

Read-only verification does not create missing evidence, advance replay, mutate
Paper Account state, or repair corruption.

## Final Verification Baseline

The final reviewed Sprint 205 CI baseline was:

- Python: `3061 passed`;
- Web: `449 passed / 47 files`;
- Ruff, package import, CLI, messages, generated-contract checks, ESLint,
  TypeScript, and production build passed;
- packaged migration-resource verification confirmed head
  `0010_strategy_order_risk` and preserved upgrades through `0009 -> 0010`.

Codex did not run Docker/Compose/container startup, volume removal, Demo reset,
or Founder Standard/Demo/browser runtime acceptance in S205. Sprint 206 is
pure documentation and does not invent a runtime-acceptance claim.

## Explicit M33 Non-Goals

M33 closes without owning or authorizing:

- accepted/routed execution orders or mutable execution status;
- fill timing, execution price, slippage, commission, fee, or tax calculation;
- partial fills, cancellation, expiry, replace, or amend;
- cash or position reservation;
- fill-caused M31 events/postings or any account mutation;
- realized/unrealized PnL, equity, market value, tax lots, or settlement;
- replay progression as part of strategy/risk evaluation;
- workers, schedulers, claims, leases, heartbeats, or continuous session loops;
- broker, QMT, MiniQMT, private-edge, live, or real-money behavior; or
- automatic strategy ranking, approval, optimization, or capital allocation.

## Known Limitations and Deferred Work

M33 intentionally supports one closed runtime family and long-only target-
position quantity semantics, one initial long-only cash risk policy family, and
one latest-trade reference-price policy. It does not pre-commit later execution
status vocabulary, fill schema, pricing/slippage model, reservation semantics,
or ledger event/posting type.

Those choices belong to M34 planning.

## Milestone 34 Handoff

Milestone 34 — Paper Execution Simulator and First True Paper Trading — is the
exact next milestone.

M34 may consume only an M33 Intent with a matching `allow`
PreTradeRiskDecision and exact verified account/market anchors. At execution
handoff M34 must revalidate freshness; M33 risk allowance is not automatically
fresh execution authorization.

M34 must define its own authority for at least:

- execution command identity;
- execution order lifecycle;
- fill timing and execution-price authority;
- rejection and partial-fill behavior;
- fees, commission, and tax treatment;
- atomic fill-to-M31-ledger postings;
- execution idempotency and reconciliation; and
- execution-time account/market freshness validation.

M34 must own any execution, fill, and ledger effects atomically and must not
mutate M33 Signal, Intent, or Decision records.

Before runtime implementation starts, M34 requires a separate CTO-owned
architecture/planning Sprint that freezes these execution boundaries.
