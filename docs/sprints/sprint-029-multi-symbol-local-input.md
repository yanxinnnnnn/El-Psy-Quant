# Sprint 29 — Multi-Symbol Local Input

## Objective

Add deterministic local multi-symbol price loading helpers.

Milestone 6 improved evaluation discipline for single-symbol research. Milestone 7 should move the project toward multi-symbol research. Sprint 29 adds the input foundation: load multiple local CSV/cache files into a stable symbol-to-prices mapping.

This sprint should not run strategies across multiple symbols, aggregate strategy results, optimize portfolios, download benchmark data, or introduce allocation logic.

## Product Goal

As the founder, I want to load multiple local price files by symbol, so future sprints can run the same research workflow across multiple symbols without relying on live downloads.

The target behavior is:

```text
symbol -> local CSV path
  -> validated prices per symbol
  -> deterministic symbol-to-prices mapping
```

and:

```text
cache_dir + symbols
  -> deterministic cache paths
  -> validated prices per symbol
  -> deterministic symbol-to-prices mapping
```

## Technical Direction

Extend the existing data package:

```text
src/
└── el_psy_quant/
    └── data/
        ├── __init__.py
        ├── cache.py
        ├── csv.py
        ├── multi.py
        ├── providers.py
        └── workflows.py

tests/
└── test_data_multi.py
```

Reuse existing functions where possible:

- `load_daily_prices_csv`
- `read_daily_prices_cache`

Keep this deterministic and local-only.

## Implementation Scope

### 1. Add Multi-CSV Loader

Implement:

```python
def load_daily_prices_csvs(
    paths_by_symbol: Mapping[str, str | Path],
) -> dict[str, pd.DataFrame]:
    ...
```

The function should:

- Accept a mapping from symbol to local CSV path.
- Reject an empty mapping with `ValueError`.
- Normalize symbols by stripping whitespace and uppercasing.
- Reject empty symbols after stripping.
- Reject duplicate normalized symbols with `ValueError`.
- Load each CSV using `load_daily_prices_csv(path)`.
- Return a plain `dict[str, pd.DataFrame]`.
- Preserve deterministic output order based on input iteration order after normalization.
- Let underlying CSV validation errors propagate with useful context if possible.

Example:

```python
prices_by_symbol = load_daily_prices_csvs(
    {
        "AAPL": "data/cache/AAPL.csv",
        "MSFT": "data/cache/MSFT.csv",
    }
)
```

Expected output keys:

```text
AAPL
MSFT
```

### 2. Add Multi-Cache Reader

Implement:

```python
def read_daily_prices_caches(
    cache_dir: str | Path,
    symbols: Iterable[str],
) -> dict[str, pd.DataFrame]:
    ...
```

The function should:

- Accept a cache directory and an iterable of symbols.
- Reject empty symbol inputs with `ValueError`.
- Normalize symbols by stripping whitespace and uppercasing.
- Reject empty symbols after stripping.
- Reject duplicate normalized symbols with `ValueError`.
- Load each symbol using `read_daily_prices_cache(cache_dir, symbol)`.
- Return a plain `dict[str, pd.DataFrame]`.
- Preserve deterministic output order based on symbol input order after normalization.
- Let missing cache files raise `FileNotFoundError`.

Example:

```python
prices_by_symbol = read_daily_prices_caches(
    "data/cache",
    ["AAPL", "MSFT"],
)
```

### 3. Export Helpers

Export both functions from:

```python
el_psy_quant.data
```

Required imports:

```python
from el_psy_quant.data import load_daily_prices_csvs, read_daily_prices_caches
```

should work.

## Validation Details

Symbol normalization should be consistent between both helpers:

```python
normalized = symbol.strip().upper()
```

Do not perform cache filename sanitization inside the multi helpers. Let existing `cache_path` / `read_daily_prices_cache` handle cache path details.

Duplicate examples that should raise:

```python
{"AAPL": "a.csv", " aapl ": "b.csv"}
```

```python
["MSFT", " msft "]
```

## Tests

Add tests covering:

### Multi-CSV Loader

- Loads multiple local CSV files into a symbol-to-DataFrame dict.
- Normalizes symbols by stripping whitespace and uppercasing.
- Preserves deterministic output order.
- Rejects empty mapping.
- Rejects empty symbol.
- Rejects duplicate normalized symbols.
- Propagates CSV validation errors.

### Multi-Cache Reader

- Loads multiple cached CSV files by symbol.
- Normalizes symbols by stripping whitespace and uppercasing.
- Preserves deterministic output order.
- Rejects empty symbol iterable.
- Rejects empty symbol.
- Rejects duplicate normalized symbols.
- Propagates missing cache files as `FileNotFoundError`.

### Export Tests

- `load_daily_prices_csvs` is exported from `el_psy_quant.data`.
- `read_daily_prices_caches` is exported from `el_psy_quant.data`.

Use deterministic temporary CSV files. No live network calls.

## README Update

Add a short example showing:

```python
from el_psy_quant.data import load_daily_prices_csvs, read_daily_prices_caches

prices_by_symbol = load_daily_prices_csvs(
    {
        "AAPL": "data/cache/AAPL.csv",
        "MSFT": "data/cache/MSFT.csv",
    }
)

cached_prices_by_symbol = read_daily_prices_caches(
    "data/cache",
    ["AAPL", "MSFT"],
)
```

Briefly state:

- Multi-symbol loading is local-only.
- It does not run strategies or allocate capital yet.

Keep it short.

## Out of Scope

- No multi-symbol strategy execution.
- No cross-symbol summary.
- No portfolio optimization.
- No capital allocation.
- No rebalancing logic.
- No benchmark comparison changes.
- No live downloads.
- No Yahoo provider changes.
- No cache writing changes.
- No CLI.
- No charts.
- No dashboards.
- No file export.
- No database.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.data import load_daily_prices_csvs, read_daily_prices_caches"` works.
- README documents the multi-symbol local input helpers briefly.
- The implementation stays deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 29 scope.
3. Do not introduce multi-symbol strategy execution, cross-symbol summaries, portfolio optimization, capital allocation, rebalancing logic, benchmark comparison changes, live downloads, Yahoo provider changes, cache writing changes, CLI commands, charts, dashboards, file exports, databases, cloud features, or broker integration.
4. Keep symbol normalization explicit and consistent.
5. Reuse existing local CSV and cache readers.
6. Keep tests deterministic and network-free.
7. Keep the PR small and reviewable.
8. Prefer the GitHub Git Data API / GitHub publish workflow over ordinary `git push` when publishing branches or opening PRs. Avoid Git smart-HTTP push if it repeatedly fails.

## Review Notes

The founder should review:

- Whether symbol normalization is intuitive.
- Whether duplicate symbol handling is strict enough.
- Whether the helpers stay local-only.
- Whether Codex avoided jumping ahead to multi-symbol strategy execution or portfolio allocation.
