"""Explicit workflows for downloading and caching market data."""

from pathlib import Path

from el_psy_quant.data.cache import write_daily_prices_cache
from el_psy_quant.data.providers import MarketDataProvider, YahooFinanceProvider


def download_daily_prices_to_cache(
    ticker: str,
    cache_dir: str | Path,
    period: str = "5y",
    provider: MarketDataProvider | None = None,
) -> Path:
    """Download daily prices and write them to the local CSV cache."""
    ticker = ticker.strip()
    if not ticker:
        raise ValueError("ticker must not be empty")
    if not period.strip():
        raise ValueError("period must not be empty")

    market_data = provider if provider is not None else YahooFinanceProvider()
    try:
        prices = market_data.download_daily_prices(ticker, period=period)
    except Exception as exc:
        raise RuntimeError(
            f"failed to download price data for {ticker}"
        ) from exc

    if prices.empty:
        raise ValueError(f"no price data downloaded for {ticker}")

    return write_daily_prices_cache(prices, cache_dir, ticker)
