# Sprint 208 — Paper Execution Order, Policy, and Lifecycle Contract Foundation

## Status

**In Progress.** GitHub Issue #409 is the authoritative implementation
specification. Issue #408 remains the authoritative M34 architecture source.

## Scope

S208 adds a pure `el_psy_quant.paper_execution` package containing:

- exact canonical `PaperExecutionBasisPoints`;
- explicit versioned `PaperExecutionPolicyReference`;
- strict M31 account, M32 market/replay, and M33 allow-decision handoff
  references;
- `CreatePaperExecutionOrderCommand` and identity-only future
  `StepPaperExecutionOrderCommand`;
- immutable deterministic `PaperExecutionOrder` and compact reference; and
- the closed derived Paper execution lifecycle/state foundation.

Order business identity includes exact immutable handoff content and excludes
actor, command idempotency key/digest, and audit timestamp. Initial state is
exactly version `0`, `working`, zero filled, requested quantity remaining, and
non-terminal.

## Authority preservation

M31 ledger/replay remains account and financial authority. M32 remains
calendar/session/event/replay and cursor authority. M33 Signal, Intent, and
Decision remain immutable upstream strategy/risk authority. Order creation
revalidates the complete current handoff and mutates none of them.

M15 execution realism and legacy M16–M19 Paper order/fill contracts remain
historical and separate.

## Explicit non-goals

S208 adds no Attempt, Fill, future-event processing, execution price,
slippage/commission/fee/tax arithmetic, execution-time risk result, M31
settlement, reservation, M32 progression, persistence, migration, API,
generated TypeScript, Web, Demo v6, worker/scheduler, broker, live, or
real-money behavior.

Migration head remains `0010_strategy_order_risk`. S209–S216 remain planned.
