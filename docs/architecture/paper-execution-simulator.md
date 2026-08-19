# Paper Execution Simulator Architecture

## Authority

GitHub Issue #408 is the authoritative Milestone 34 architecture source. This
record summarizes that approved boundary; it does not replace or broaden the
Issue.

Milestone 34 is In Progress through the approved S207–S216 sequence. S207–S211
are Complete. Sprint 212 is current, with Issue #417 as its authoritative
implementation specification.

## Authority chain

```text
M31 immutable ledger events/postings and deterministic replay
  + M32 calendar/session/event/replay authority
  + immutable M33 OrderIntent and matching allow PreTradeRiskDecision
    -> immutable M34 PaperExecutionOrder
      -> S209 PaperExecutionAttempt
        -> S209 PaperExecutionFill
          -> S210 pure M31 execution event and postings
          -> S210 ExecutionSettlementLink
```

Each layer remains separate. M34 does not repurpose the M15
`el_psy_quant.execution.OrderIntent`, legacy M16–M19 `PaperOrderRecord` or
`PaperFill`, or the M33 `OrderIntent` as execution authority. An M33 allow
Decision is historical evidence over one exact snapshot, not permanent
execution authorization.

## Delivered S208–S211 boundary

Sprint 208 added the pure `el_psy_quant.paper_execution` domain-contract
foundation:

- exact canonical basis-points values;
- one explicit versioned Paper execution-policy reference;
- exact immutable M31, M32, and matching M33 allow handoff references;
- create-order and future step-command identities;
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

Sprint 209 adds pure/in-memory one-event execution over that foundation:

- exact compact consumed-event and cursor-transition evidence;
- immutable deterministic Attempt and unsettled Fill authority;
- `consumed_trade_event_price_v1` plus exact fixed-bps slippage;
- independently rounded `per_fill_bps_costs_v1` evidence;
- execution-time `long_only_cash_risk_v1` revalidation evidence;
- full, partial, no-fill, risk-reject, replay-exhaustion, and session-exhaustion
  outcomes; and
- strict lifecycle reconstruction from immutable Attempt/Fill history.

In-session progression uses M32 `MarketDataReplayEngine.next_event()` exactly
once. Boundary attempts do not consume an event. No durable replay checkpoint
exists yet.

Sprint 210 adds pure/in-memory settlement semantics:

- one Fill creates one `execution_fill_posted` M31 event;
- that event owns exactly one `execution_settlement` cash posting and one
  `execution_fill` position posting;
- buy debits and capitalized costs and sell proportional average-cost removal
  are exact and fail closed;
- M31 replay remains financial/account authority; and
- one deterministic `ExecutionSettlementLink` provides non-financial
  one-to-one Fill/event/posting reconciliation evidence.

Sprint 211 adds five append-only M34 tables, strict reconstruction, scoped
command receipts, one-winner SQLite create/step transactions, M31/M32 CAS
integration, and read-only whole-order reconciliation. One successful step is
one atomic durable commit.

## Deferred authority

S211 durably commits the pure S209/S210 evidence without duplicating its math.
S212 exposes that authority through exactly nine authenticated versioned
operations, strict generated contracts, stable public errors, and bounded
audit correlation. Reservation, Web, Demo v6, worker, scheduler, broker, live,
and real-money behavior remain deferred.

The migration head is exactly `0011_paper_execution`.

## Preserved runtime boundary

M34 remains a manual synchronous simulator. S213–S216 remain planned. M35
owns durable runtime and recovery; M36 owns multi-session and multi-day
operation. Neither later milestone is implemented here.
