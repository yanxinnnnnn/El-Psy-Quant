# Sprint 13 — Data Cache Foundation

## Objective

Add a small deterministic local data cache foundation.

Milestone 2 gave us local CSV loading and CSV-based research examples. Sprint 13 should add explicit cache read/write helpers so downloaded or prepared daily price data can be persisted locally and reused later, without introducing automatic downloads, databases, Parquet, or a larger data platform.

## Product Goal

As the founder, I want a simple local CSV cache utility so research data can be saved and loaded reproducibly using a predictable file layout.

The target flow is:

```text
prices DataFrame
  -> write_daily_prices_cache
  -> local cache CSV
  -> read_daily_prices_cache
  -> prices DataFrame
```

This sprint is about cache mechanics only. It is not about fetching live data yet.

## Technical Direction

Extend the data module with cache helpers:

```text
src/
└── el_psy_quant/
    └── data/
        ├── __init__.py
        ├── csv.py
        ├── providers.py
        └── cache.py

tests/
└── test_data_cache.py
```

Keep the cache implementation explicit, local, and file-based.

Prefer small functions over classes.

## Implementation Scope

### Must Have

Implement:

```python
def cache_path(cache_dir: str | Path, symbol: str) -> Path:
    ...


def write_daily_prices_cache(
    prices: pd.DataFrame,
    cache_dir: str | Path,
    symbol: str,
) -> Path:
    ...


def read_daily_prices_cache(cache_dir: str | Path, symbol: str) -> pd.DataFrame:
    ...
```

### `cache_path`

The function should:

- Accept `str` or `pathlib.Path` for `cache_dir`.
- Accept a non-empty `symbol` string.
- Normalize the symbol into a safe filename.
- Return a path like:

```text
<cache_dir>/<normalized_symbol>.csv
```

Suggested normalization:

- Strip leading/trailing whitespace.
- Convert to uppercase.
- Replace `/`, `\\`, `:`, and whitespace with `_`.
- Reject empty symbols with `ValueError`.

Examples:

```text
"aapl"       -> AAPL.csv
"BRK/B"      -> BRK_B.csv
"  msft  "   -> MSFT.csv
"BTC-USD"    -> BTC-USD.csv
```

### `write_daily_prices_cache`

The function should:

- Accept a daily prices DataFrame indexed by date.
- Require columns:
  - `Open`
  - `High`
  - `Low`
  - `Close`
  - `Volume`
- Reject empty DataFrames with `ValueError`.
- Reject missing required columns with `ValueError`.
- Reject NaN values in `Close` with `ValueError`.
- Require a `DatetimeIndex`; raise `ValueError` otherwise.
- Reject duplicate index values with `ValueError`.
- Sort rows by date ascending before writing.
- Create `cache_dir` if it does not exist.
- Write CSV with a `Date` column compatible with `load_daily_prices_csv`.
- Return the written file path.

### `read_daily_prices_cache`

The function should:

- Resolve the cache file path using `cache_path`.
- Raise `FileNotFoundError` if the cache file does not exist.
- Load the file using the existing `load_daily_prices_csv` function.
- Return the loaded DataFrame.

## Tests

Add tests covering:

- `cache_path` creates expected filenames for normal symbols.
- `cache_path` normalizes lowercase symbols to uppercase.
- `cache_path` replaces unsafe characters and whitespace with `_`.
- Empty symbols raise `ValueError`.
- `write_daily_prices_cache` writes a CSV file and returns its path.
- `write_daily_prices_cache` creates the cache directory if needed.
- Written cache can be read back with `read_daily_prices_cache`.
- Written rows are sorted ascending by date.
- Missing required price columns raise `ValueError`.
- Empty DataFrame raises `ValueError`.
- Non-DatetimeIndex raises `ValueError`.
- Duplicate dates raise `ValueError`.
- NaN `Close` raises `ValueError`.
- `read_daily_prices_cache` raises `FileNotFoundError` for a missing cache file.
- Functions are exported from `el_psy_quant.data`.

Use pytest `tmp_path` for all cache tests.

## README Update

Add a small example showing:

```python
from el_psy_quant.data import read_daily_prices_cache, write_daily_prices_cache

path = write_daily_prices_cache(prices, "data/cache", "AAPL")
cached_prices = read_daily_prices_cache("data/cache", "AAPL")
```

Keep the example short. Do not turn README into a cache tutorial.

## Out of Scope

- No live Yahoo Finance download integration.
- No automatic refresh.
- No cache expiration.
- No metadata sidecar files.
- No databases.
- No Parquet.
- No compression.
- No multi-symbol batch cache.
- No provider classes.
- No CLI.
- No pipeline changes required.
- No trading calendar logic.
- No adjusted-price logic.
- No split/dividend handling.
- No cloud storage.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.data import cache_path, write_daily_prices_cache, read_daily_prices_cache"` works.
- README includes a short cache usage example.
- The implementation is deterministic, local-only, and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 13 scope.
3. Do not introduce live downloads, automatic refresh, cache expiration, metadata sidecars, databases, Parquet, compression, provider classes, CLI parsing, pipeline changes, trading calendars, adjusted-price logic, split/dividend handling, cloud storage, dashboards, or broker integration.
4. Reuse `load_daily_prices_csv` when reading cached files.
5. Use temporary directories in tests.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether cache filenames are deterministic and safe.
- Whether cache writing produces files readable by the existing CSV loader.
- Whether invalid data is rejected before being cached.
- Whether Codex avoided turning this into a full data platform.