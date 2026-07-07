# Sprint 71 — Execution Assumptions Foundation

## Objective

Define the smallest useful execution-assumption boundary for local deterministic backtests.

## Delivered Scope

Sprint 71 adds `el_psy_quant.execution` with a frozen `ExecutionAssumptions`
object and small helper functions for validation and defaults.

The boundary records three explicit choices:

- `timing`
- `price_field`
- `missing_price_policy`

String fields are trimmed and lowercased so deterministic callers can pass
human-friendly values without changing the stored representation.

## Accepted Values

Supported timing values:

- `same_bar`
- `next_bar`

Supported price fields:

- `open`
- `high`
- `low`
- `close`

Supported missing price policies:

- `raise`

Unsupported values raise `ValueError`.

## Conservative Default

`default_execution_assumptions()` returns:

```text
next_bar + open + raise
```

This is conservative because it avoids same-bar look-ahead assumptions, uses the
next bar's open as the earliest deterministic fill reference after a signal, and
fails loudly when required prices are missing.

## Representation

`ExecutionAssumptions.to_dict()` returns a small JSON-compatible dictionary:

```python
{
    "timing": "next_bar",
    "price_field": "open",
    "missing_price_policy": "raise",
}
```

## Out of Scope

- Order intent models.
- Fill models or fill price lookup.
- Execution-adjusted trade summaries.
- Execution realism artifacts.
- YAML, CLI, manifest, metrics, or configured-run schema changes.
- Broker, exchange, paper-trading, or live-trading integration.
