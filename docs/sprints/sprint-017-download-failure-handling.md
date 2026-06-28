# Sprint 17 — Download Failure Handling

## Objective

Improve the error handling around live market data downloads.

During local testing, `yfinance` returned a rate-limit error and the provider produced an empty DataFrame. The current cache writer correctly rejects empty data with `ValueError("prices must not be empty")`, but that message is too low-level for a user who called the download workflow.

Sprint 17 should make live download failures easier to understand without adding retry logic, rate-limit handling, cache refresh, or provider complexity.

## Product Goal

As the founder, I want the Yahoo-to-cache workflow to fail with a clear user-facing error when the provider fails or returns no data, so I can quickly understand whether the issue is download-side rather than cache-side.

The target behavior is:

```text
download_daily_prices_to_cache("AAPL", "data/cache")
  -> provider fails or returns empty data
  -> clear download-level error
  -> no cache file is written
```

## Technical Direction

Improve the existing data workflow:

```text
src/
└── el_psy_quant/
    └── data/
        ├── __init__.py
        ├── cache.py
        ├── providers.py
        └── workflows.py

tests/
└── test_data_workflows.py
```

Keep this as a small workflow-level improvement.

Do not rewrite the provider abstraction.

## Implementation Scope

### Must Have

Update:

```python
def download_daily_prices_to_cache(
    ticker: str,
    cache_dir: str | Path,
    period: str = "5y",
    provider: MarketDataProvider | None = None,
) -> Path:
    ...
```

The function should still:

- Validate non-empty `ticker` before calling the provider.
- Validate non-empty `period` before calling the provider.
- Use the injected provider when supplied.
- Use `YahooFinanceProvider()` when no provider is supplied.
- Call `provider.download_daily_prices(ticker, period=period)`.
- Write successful non-empty data through `write_daily_prices_cache`.
- Return the written cache path.

Add clearer handling for these cases:

### Empty Download Result

If the provider returns an empty DataFrame, raise a clear download-level error before calling `write_daily_prices_cache`.

Suggested message:

```text
no price data downloaded for AAPL
```

The exact exception type may be `ValueError` unless a very small custom exception is clearly justified. Do not add a new error hierarchy.

### Provider Exception

If the provider raises an exception, wrap it with a clearer workflow-level message while preserving the original exception as the cause.

Suggested message:

```text
failed to download price data for AAPL
```

Example implementation shape:

```python
try:
    prices = market_data.download_daily_prices(ticker, period=period)
except Exception as exc:
    raise RuntimeError(f"failed to download price data for {ticker}") from exc
```

Do not catch exceptions from `write_daily_prices_cache`. Cache validation errors should still come from the cache layer.

## Tests

Add or update tests covering:

- Successful provider result still writes a cache file and returns the path.
- Empty provider result raises a clear error mentioning the ticker.
- Empty provider result does not write a cache file.
- Provider exception is wrapped with a clear error mentioning the ticker.
- The original provider exception is preserved as `__cause__`.
- Provider exception does not write a cache file.
- Empty ticker still raises before provider call.
- Empty period still raises before provider call.
- Successful workflow still uses `write_daily_prices_cache` behavior.
- No test calls Yahoo Finance or any live network service.

Use fake providers and pytest `tmp_path`.

## README Update

Add a short note under the Yahoo-to-cache section explaining:

- This workflow performs a live download.
- Live providers can fail or be rate-limited.
- Failed or empty downloads are not written to the local cache.

Keep the note short.

## Out of Scope

- No retry logic.
- No exponential backoff.
- No rate-limit handling.
- No yfinance-specific exception imports.
- No automatic cache fallback.
- No cache freshness checks.
- No cache expiration.
- No metadata sidecar files.
- No provider class redesign.
- No start/end date support.
- No multi-symbol downloads.
- No CLI.
- No pipeline changes.
- No charts.
- No dashboards.
- No broker integration.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "from el_psy_quant.data import download_daily_prices_to_cache"` works.
- README documents that live download failures are not cached.
- Tests remain deterministic and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 17 scope.
3. Do not introduce retry logic, backoff, rate-limit handling, yfinance-specific exception imports, automatic cache fallback, cache freshness checks, cache expiration, metadata sidecars, provider redesign, start/end date support, multi-symbol downloads, CLI parsing, pipeline changes, charts, dashboards, cloud features, or broker integration.
4. Use fake providers in tests. Do not call Yahoo Finance or any live network service.
5. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether empty downloads fail at the workflow layer with a clear message.
- Whether provider exceptions preserve the original cause.
- Whether failed downloads avoid writing cache files.
- Whether Codex avoided turning this into a retry/rate-limit framework.