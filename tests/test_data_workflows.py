from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.data import (
    download_daily_prices_to_cache,
    read_daily_prices_cache,
)


def make_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0],
            "High": [102.0],
            "Low": [99.0],
            "Close": [101.0],
            "Volume": [1_000],
        },
        index=pd.to_datetime(["2024-01-02"]),
    )


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def download_daily_prices(
        self, ticker: str, period: str = "5y"
    ) -> pd.DataFrame:
        self.calls.append((ticker, period))
        return make_prices()


def test_downloads_prices_writes_cache_and_returns_path(tmp_path: Path) -> None:
    provider = FakeProvider()

    path = download_daily_prices_to_cache(
        "AAPL", tmp_path, period="1y", provider=provider
    )

    assert provider.calls == [("AAPL", "1y")]
    assert path == tmp_path / "AAPL.csv"
    assert path.is_file()
    pd.testing.assert_frame_equal(
        read_daily_prices_cache(tmp_path, "AAPL"),
        make_prices().rename_axis("Date"),
    )


def test_strips_ticker_before_download_and_cache_write(tmp_path: Path) -> None:
    provider = FakeProvider()

    path = download_daily_prices_to_cache("  aapl  ", tmp_path, provider=provider)

    assert provider.calls == [("aapl", "5y")]
    assert path == tmp_path / "AAPL.csv"


@pytest.mark.parametrize(
    ("ticker", "period", "message"),
    [("   ", "5y", "ticker"), ("AAPL", "   ", "period")],
)
def test_rejects_empty_input_before_calling_provider(
    tmp_path: Path, ticker: str, period: str, message: str
) -> None:
    provider = FakeProvider()

    with pytest.raises(ValueError, match=f"{message} must not be empty"):
        download_daily_prices_to_cache(
            ticker, tmp_path, period=period, provider=provider
        )

    assert provider.calls == []


def test_uses_yahoo_provider_when_provider_is_omitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = FakeProvider()
    monkeypatch.setattr(
        "el_psy_quant.data.workflows.YahooFinanceProvider", lambda: provider
    )

    download_daily_prices_to_cache("AAPL", tmp_path)

    assert provider.calls == [("AAPL", "5y")]


def test_workflow_is_exported_from_data_package() -> None:
    from el_psy_quant import data

    assert data.download_daily_prices_to_cache is download_daily_prices_to_cache
