# Sprint 97 — Paper Workflow Config Contract Foundation

## Status

Complete.

## Goal

Add the smallest optional local YAML config contract for explicit paper-run inputs.

Sprint 97 starts Milestone 19 by making configured paper workflow inputs parseable and validated without executing any paper workflow.

## Delivered

- Added optional `paper_run` support to local experiment configuration.
- Added `PaperRunConfig` as the typed validated config boundary.
- Kept existing research-only configs backward compatible by defaulting `paper_run` to `None`.
- Validated explicit paper run identity, creation timestamp, starting and ending account states, paper order records, and paper fills.
- Reused existing paper-domain constructors and validation where practical.
- Added deterministic tests for valid paper-run config, invalid required fields, invalid account states, invalid orders, invalid fills, and public config exports.

## Config Shape

The optional section is local and explicit:

```yaml
paper_run:
  run_id: paper-run-001
  created_timestamp: "2026-07-08T00:00:00Z"
  starting_account_state:
    timestamp: "2026-07-08T00:00:00Z"
    starting_cash: 10000.0
    current_cash: 10000.0
    positions:
      AAPL: 0.0
  ending_account_state:
    timestamp: "2026-07-08T00:01:00Z"
    starting_cash: 10000.0
    current_cash: 9900.0
    positions:
      AAPL: 1.0
  orders:
    - order_id: order-001
      timestamp: "2026-07-08T00:00:30Z"
      symbol: AAPL
      side: buy
      quantity: 1.0
      status: filled
  fills:
    - timestamp: "2026-07-08T00:00:45Z"
      symbol: AAPL
      side: buy
      quantity: 1.0
      price: 100.0
      order_id: order-001
```

## Scope Boundaries

This sprint only defines and validates the config contract.

It does not add:

- paper workflow execution
- `PaperRunRequest` construction
- file writing or reading
- output layout changes
- manifest wiring
- CLI expansion
- broker, live, scheduler, database, dashboard, or reporting behavior
- automatic research-to-paper promotion

## Next Step

Sprint 98 — Configured Paper Request Boundary Foundation should convert the validated `paper_run` config boundary into a `PaperRunRequest` without introducing strategy-signal-to-order automation.
