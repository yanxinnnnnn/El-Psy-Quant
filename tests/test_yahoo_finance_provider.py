import pandas as pd

from el_psy_quant.data.providers import YahooFinanceProvider


def test_yahoo_provider_delegates_to_yfinance(monkeypatch) -> None:
    expected_columns = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    expected = pd.DataFrame([[99.0, 101.0, 98.0, 100.0, 100.0, 1_000]], columns=expected_columns)
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_download(ticker: str, **kwargs: object) -> pd.DataFrame:
        calls.append((ticker, kwargs))
        return expected

    monkeypatch.setattr("el_psy_quant.data.providers.yf.download", fake_download)

    result = YahooFinanceProvider().download_daily_prices("AAPL", period="1y")

    assert result is expected
    assert list(result.columns) == expected_columns
    assert calls == [
        (
            "AAPL",
            {
                "period": "1y",
                "interval": "1d",
                "auto_adjust": False,
                "multi_level_index": False,
                "progress": False,
            },
        )
    ]
