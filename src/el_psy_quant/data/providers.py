"""Interfaces and implementations for loading market data."""

from typing import Protocol

import pandas as pd
import yfinance as yf


class MarketDataProvider(Protocol):
    """Interface for a source of daily market prices."""

    def download_daily_prices(
        self, ticker: str, period: str = "5y"
    ) -> pd.DataFrame:
        """Download daily OHLCV prices for a ticker."""
        ...


class YahooFinanceProvider:
    """Load daily market prices from Yahoo Finance."""

    def download_daily_prices(
        self, ticker: str, period: str = "5y"
    ) -> pd.DataFrame:
        """Download daily OHLCV prices using yfinance."""
        return yf.download(
            ticker,
            period=period,
            interval="1d",
            auto_adjust=False,
            multi_level_index=False,
            progress=False,
        )
