# Sprint 142 — Paper Run Application Command Boundary

## Status

Complete.

## Objective

Expose the existing explicit-input paper-run execution boundary through one thin synchronous application command and one versioned API endpoint.

## Delivered Boundary

Sprint 142 adds immutable command inputs, explicit immutable product views, a sanitized application error, strict request schemas, explicit response schemas, and exactly one production endpoint:

```text
POST /api/v1/paper-runs
```

The caller supplies:

- a caller-owned `run_id` and created timestamp
- explicit starting and ending paper account states
- explicit orders in caller order
- explicit fills in caller order

The application command reconstructs domain objects through:

```text
create_paper_account_state(...)
create_paper_order_record(...)
create_paper_fill(...)
create_paper_run_request(...)
run_paper_trading_request(...)
```

These existing paper boundaries remain authoritative for timestamp, cash, position, symbol, side, status, quantity, price, order-ID, request, session-summary, and artifact behavior. The response contains the normalized in-memory artifact with deterministic domain position ordering and caller order preserved for orders and fills.

## Execution Semantics

The HTTP request waits for local execution to complete and returns HTTP 200 on success. The workflow packages explicit values only. It does not generate strategy signals or orders, create or apply fills, derive or reconcile the ending state, require fill-to-order consistency beyond existing domain rules, or communicate with a market-data or execution service.

An absent fill `order_id` remains `null`. A repeated `run_id` is accepted because it is domain identity, not a server-generated durable job ID, and Sprint 142 has no registry.

## Errors

Structurally valid commands rejected by existing paper-domain construction or execution return:

```text
HTTP 422
paper_run_invalid
Paper run request is invalid
```

Malformed JSON request shapes, unknown fields, wrong arrays or objects, and boolean numeric inputs continue to use the existing sanitized `request_validation_error` envelope. Server-owned request IDs remain consistent between response headers and error bodies.

## Guardrails

Sprint 142 is synchronous and in-memory only. It adds no:

- filesystem input or output, artifact root, path input, artifact persistence, or result-summary writing
- configured-paper, YAML, research, backtest, strategy-signal, or automatic order workflow execution
- durable job, mutable status, idempotency, polling, retry, cancellation, recovery, worker, scheduler, or queue
- repository, SQLite, SQLAlchemy, migration, or database behavior
- paper-run list, detail, status, raw, file, or download endpoint
- lifecycle proposal or review command, automatic transition, approval, or rejection
- broker, QMT, MiniQMT, market-data stream, live, real-money, or capital-allocation behavior

## Next Step

```text
Sprint 143 — Lifecycle Proposal and Human Review Application Commands
```
