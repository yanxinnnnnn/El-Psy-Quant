# Sprint 14 — Yahoo-to-CSV Cache Workflow

## Objective

Connect the existing live market data provider to the local CSV cache layer.

Sprint 13 added deterministic cache read/write helpers. Sprint 14 should add a small explicit workflow that downloads daily prices through the existing market data provider interface and writes the result to the local CSV cache.

This sprint bridges live data and reproducible local research, without adding automatic refresh, cache expiration, CLI commands, or pipeline changes.

## Product Goal

As the founder, I want a simple workflow that can fetch daily market data once and persist it into the local cache, so later research can run from stable CSV files.

The target flow is:

```text
MarketDataProvider / YahooFinanceProvider
  -> download daily prices
  -> write_daily_prices_cache
  -> local CSV cache
  -> read_daily_prices_cache
  -> reproducible local research
```

## Technical Direction

Add a small workflow module under the data package:

```text
src/
└── el_psy_quant/
    └── data/
        ├── __init__.py
        ├── cache.py
        ├── csv.py
        ├── providers.py
        └── workflows.py

tests/
└── test_data_workflows.py
```

Keep this as a function, not a class.

The existing provider API is:

```python
def download_daily_prices(self, ticker: str, period: str = "5y") -> pd.DataFrame:
    ...
```

Do not invent `start` / `end` parameters in this sprint.

## Implementation Scope

### Must Have

Implement:

```python
def download_daily_prices_to_cache(
    ticker: str,
    cache_dir: str | Path,
    period: str = "5y",
    provider: MarketDataProvider | None = None,
) -> Path:
    ...
```

The function should:

- Accept a non-empty `ticker` string.
- Strip leading/trailing whitespace from `ticker` before use.
- Accept `cache_dir` as `str` or `pathlib.Path`.
- Accept `period`, defaulting to `"5y"`.
- Reject empty `ticker` with `ValueError` before calling any provider.
- Reject empty `period` with `ValueError` before calling any provider.
- Use the provided `provider` if passed.
- Use `YahooFinanceProvider()` if `provider` is `None`.
- Call `provider.download_daily_prices(ticker, period=period)`.
- Write the returned DataFrame with `write_daily_prices_cache(prices, cache_dir, ticker)`.
- Return the written cache path.
- Export the function from `el_psy_quant.data`.

### Important Design Rule

This function is an explicit workflow.

It should perform a download only when called directly. It should not automatically refresh cache files, decide freshness, schedule downloads, or hide network behavior behind other functions.

## Tests

Add tests covering:

- The function calls the provided fake provider with the expected `ticker` and `period`.
- The function writes a cache file and returns the path.
- The written cache can be read back with `read_daily_prices_cache`.
- Leading/trailing whitespace in `ticker` is stripped before provider call and cache write.
- Empty `ticker` raises `ValueError` and does not call the provider.
- Empty `period` raises `ValueError` and does not call the provider.
- If `provider` is omitted, `YahooFinanceProvider` is instantiated. Use monkeypatching; do not make a live network call.
- The function is exported from `el_psy_quant.data`.

Use a fake provider in tests. Do not call Yahoo Finance or any live network service in tests.

## README Update

Add a short example showing:

```python
from el_psy_quant.data import download_daily_prices_to_cache, read_daily_prices_cache

path = download_daily_prices_to_cache("AAPL", "data/cache", period="5y")
prices = read_daily_prices_cache("data/cache", "AAPL")
```

Keep it short and make it clear that this workflow performs a live download when called.

## Out of Scope

- No CLI command.
- No scheduled refresh.
- No automatic cache freshness checks.
- No cache expiration.
- No metadata sidecar files.
- No start/end date support.
- No multi-symbol batch download.
- No retry logic.
- No rate-limit handling.
- No provider class changes unless strictly necessary.
- No pipeline changes.
- No charts.
- No dashboards.
- No broker integration.
- No cloud storage.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.data import download_daily_prices_to_cache"` works.
- README includes a short Yahoo-to-cache usage example.
- Tests remain deterministic and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 14 scope.
3. Do not introduce CLI commands, scheduled refresh, cache freshness checks, expiration, metadata sidecars, start/end date support, multi-symbol batch downloads, retry logic, rate-limit handling, pipeline changes, charts, dashboards, cloud storage, or broker integration.
4. Reuse `write_daily_prices_cache` and `read_daily_prices_cache` behavior rather than duplicating cache logic.
5. Use fake providers and monkeypatching in tests. Do not call Yahoo Finance in tests.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether the workflow clearly separates live download from local cache usage.
- Whether tests avoid all network calls.
- Whether provider injection is used for testability.
- Whether Codex avoided turning this into a data platform or CLI.