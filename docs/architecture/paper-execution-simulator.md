# Paper Execution Simulator Architecture

## Authority

GitHub Issue #408 is the authoritative Milestone 34 architecture source. This
record summarizes that approved boundary; it does not replace or broaden the
Issue.

Milestone 34 is Complete after the Sprint 216 closeout PR is merged. S207–S215
are Complete and Sprint 216 is the current documentation-only closeout under
Issue #425. The canonical closeout is:

```text
docs/closeouts/milestone-034-paper-execution-simulator-and-first-true-paper-trading-closeout.md
```

## Authority chain

```text
M31 immutable ledger events/postings and deterministic replay
  + M32 calendar/session/event/replay authority
  + immutable M33 OrderIntent and matching allow PreTradeRiskDecision
    -> immutable M34 PaperExecutionOrder
      -> immutable PaperExecutionAttempt
        -> optional immutable PaperExecutionFill
          -> one atomic M31 execution event and postings
          -> one ExecutionSettlementLink
      -> exact M32 cursor progression when an event is consumed
```

Each layer remains separate. M34 does not repurpose the M15
`el_psy_quant.execution.OrderIntent`, legacy M16–M19 `PaperOrderRecord` or
`PaperFill`, or the M33 `OrderIntent` as execution authority. An M33 allow
Decision is historical evidence over one exact snapshot, not permanent
execution authorization.

## Delivered M34 boundary

Sprint 208 added the pure `el_psy_quant.paper_execution` domain-contract
foundation:

- exact canonical basis-points values;
- one explicit versioned Paper execution-policy reference;
- exact immutable M31, M32, and matching M33 allow handoff references;
- create-order and step-command identities;
- deterministic immutable `PaperExecutionOrder` authority and compact
  reference; and
- a closed derived lifecycle/state vocabulary.

Order creation revalidates exact current M31/M32/M33 authority. It copies side
and requested quantity only from the validated M33 Intent, creates no
reservation, does not mutate an account, and does not advance replay.

The v1 lifecycle vocabulary is exactly:

```text
working
partially_filled
filled
rejected
partially_filled_rejected
```

Initial derived state is execution version `0`, `working`, zero cumulative
fill, full remaining quantity, and non-terminal.

Sprint 209 added pure one-event execution:

- exact compact consumed-event and cursor-transition evidence;
- immutable deterministic Attempt and unsettled Fill authority;
- `consumed_trade_event_price_v1` plus exact fixed-bps slippage;
- independently rounded `per_fill_bps_costs_v1` evidence;
- execution-time `long_only_cash_risk_v1` revalidation evidence;
- full, partial, no-fill, risk-reject, replay-exhaustion, and session-exhaustion
  outcomes; and
- strict lifecycle reconstruction from immutable Attempt/Fill history.

In-session progression uses M32 `MarketDataReplayEngine.next_event()` exactly
once. Boundary attempts do not consume an out-of-session event.

Sprint 210 added Fill-to-M31 settlement semantics:

- one Fill creates one `execution_fill_posted` M31 event;
- that event owns exactly one `execution_settlement` cash posting and one
  `execution_fill` position posting;
- buy debits/capitalized costs and sell proportional average-cost removal are
  exact and fail closed;
- M31 replay remains financial/account authority; and
- one deterministic `ExecutionSettlementLink` provides non-financial one-to-one
  Fill/event/posting reconciliation evidence.

Sprint 211 added five append-only M34 tables, strict historical/live
reconstruction, scoped command receipts, one-winner SQLite Create/Step
transactions, M31/M32 CAS integration, and read-only whole-order reconciliation.
One successful Step is one atomic durable commit across M34, M31, M32, and the
receipt namespace.

Sprint 212 exposes that authority through exactly nine authenticated versioned
operations, strict public schemas, stable errors/audit, canonical OpenAPI, and
generated TypeScript contracts.

Sprint 213 adds one bilingual generated-contract-only Founder workspace for
explicit manual Order creation, one-event Step, historical evidence inspection,
and reconciliation without browser financial/execution/risk math.

Sprint 214 adds Demo v6 end-to-end first-true-paper-trading evidence through
merged application paths. The manual scenario remains fresh until the Founder
acts; completed, execution-risk-rejection, and exhaustion scenarios are
prebuilt only through normal product authority paths.

Sprint 215 adversarially hardened restart, idempotency, concurrency, SQLite
busy behavior, populated `0010 -> 0011` upgrade, transaction rollback,
corruption/no-repair, API error surfaces, and Standard/Demo isolation without
requiring a new production behavior path.

The migration head is exactly:

```text
0011_paper_execution
```

Demo source/descriptor/dataset remains v6.

## Preserved runtime boundary

M34 closes as a manual synchronous simulator. It owns execution/fill truth and
atomic fill-caused M31 effects, but not continuous runtime orchestration.

M35 — Durable Paper Runtime and Recovery — is the exact next milestone and must
reuse the M34 one-event Step primitive rather than invent a second execution
path. Durable claims/leases, start/stop/resume controls, repeated Step loops,
heartbeats/stale-work detection, interruption recovery/checkpoints, operational
reconciliation, and bounded observability require the next CTO planning gate:

```text
Sprint 217 — Plan Milestone 35: Durable Paper Runtime and Recovery
```

M36 remains the future multi-session and multi-day Paper Trading operations and
acceptance milestone. Reservation expansion, broker, live, and real-money
behavior remain outside this architecture unless a later authoritative
milestone explicitly approves them.
