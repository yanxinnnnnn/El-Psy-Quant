# Sprint 11 — Local CSV Data Loader

## Objective

Add the first deterministic local data input path.

Sprint 10 added an in-memory local research example. Sprint 11 should let El-Psy-Quant load daily price data from a local CSV file, without introducing caching, live downloads, databases, or a larger data-provider framework.

## Product Goal

As the founder, I want a simple CSV loader so research can run from reproducible local data files instead of hardcoded price series or live network calls.

The target flow is:

```text
local CSV
  -> daily prices DataFrame
  -> close prices
  -> moving_average_crossover_pipeline
  -> backtest_summary
```

## Technical Direction

Extend the data module with a local CSV loader:

```text
src/
└── el_psy_quant/
    └── data/
        ├── __init__.py
        ├── providers.py
        └── csv.py

tests/
└── test_data_csv.py
```

Prefer a small function over a provider class for this sprint.

The function should be local, deterministic, and easy to test.

## Implementation Scope

### Must Have

Implement:

```python
def load_daily_prices_csv(path: str | Path) -> pd.DataFrame:
    ...
```

The function should:

- Accept `str` or `pathlib.Path`.
- Read a local CSV file with `pandas.read_csv`.
- Require these columns:
  - `Date`
  - `Open`
  - `High`
  - `Low`
  - `Close`
  - `Volume`
- Allow optional columns such as `Adj Close`.
- Parse `Date` into a `DatetimeIndex`.
- Sort rows by date ascending.
- Preserve price/volume columns in the returned DataFrame.
- Reject missing required columns with `ValueError`.
- Reject invalid dates with `ValueError`.
- Reject duplicate dates with `ValueError`.
- Reject NaN values in the `Close` column with `ValueError`.
- Return a `pd.DataFrame` indexed by date.
- Export the function from `el_psy_quant.data`.

### Example CSV

```csv
Date,Open,High,Low,Close,Volume
2024-01-01,100,110,99,105,1000
2024-01-02,105,112,104,110,1200
```

Expected result:

- Index: `DatetimeIndex` from the `Date` column.
- Columns include at least `Open`, `High`, `Low`, `Close`, `Volume`.
- Rows sorted ascending by date.

## Tests

Add tests covering:

- Loading a valid CSV.
- Returned index is a `DatetimeIndex`.
- Rows are sorted by date ascending.
- Required price columns are preserved.
- Optional `Adj Close` column is preserved if present.
- Missing required columns raise `ValueError`.
- Invalid dates raise `ValueError`.
- Duplicate dates raise `ValueError`.
- NaN `Close` values raise `ValueError`.
- Function accepts a `Path` object.
- Function is exported from `el_psy_quant.data`.

Use pytest `tmp_path` to create test CSV files.

## README Update

Add a small example showing:

```python
from el_psy_quant.data import load_daily_prices_csv

prices = load_daily_prices_csv("data/sample_prices.csv")
close = prices["Close"]
```

Do not add real CSV data files in this sprint unless strictly necessary for the README example.

## Out of Scope

- No live Yahoo Finance download integration.
- No data cache.
- No automatic CSV writing.
- No sample data directory unless tests need temporary files.
- No multi-symbol batch loader.
- No database.
- No Parquet.
- No time zone handling.
- No adjusted-price logic.
- No split/dividend processing.
- No trading calendar logic.
- No CLI.
- No charts.
- No pipeline changes required.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.data import load_daily_prices_csv"` works.
- README includes a small CSV-loading usage example.
- The loader is deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 11 scope.
3. Do not introduce live downloads, caching, provider classes, databases, Parquet, time zone logic, adjusted-price logic, split/dividend handling, trading calendars, CLI parsing, charts, pipeline changes, cloud features, or broker integration.
4. Keep the function deterministic and easy to test.
5. Use temporary CSV files in tests rather than committing large data files.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether the loader is simple and predictable.
- Whether required schema validation is explicit.
- Whether date handling is safe enough for early research.
- Whether Codex avoided building a data framework too early.