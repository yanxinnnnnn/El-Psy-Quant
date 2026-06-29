from pathlib import Path

import pandas as pd
import pytest

from el_psy_quant.backtesting import compare_to_buy_and_hold_benchmark


def write_benchmark(path: Path, dates: list[str], close: list[float]) -> None:
    pd.DataFrame(
        {
            "Date": dates,
            "Open": close,
            "High": close,
            "Low": close,
            "Close": close,
            "Volume": [100] * len(close),
        }
    ).to_csv(path, index=False)


def make_result(include_net: bool = True) -> pd.DataFrame:
    index = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
    result = pd.DataFrame(
        {
            "equity": [100.0, 105.0, 110.0],
            "strategy_return": [0.0, 0.05, 0.047619],
        },
        index=index,
    )
    if include_net:
        result["net_strategy_return"] = [0.0, 0.04, 0.03]
    return result


def test_returns_aligned_strategy_benchmark_and_excess_metrics(
    tmp_path: Path,
) -> None:
    path = tmp_path / "benchmark.csv"
    write_benchmark(
        path,
        ["2023-12-31", "2024-01-02", "2024-01-03"],
        [80.0, 100.0, 110.0],
    )

    comparison = compare_to_buy_and_hold_benchmark(
        make_result(), path, initial_capital=1_000.0
    )

    assert comparison["strategy_periods"] == 2.0
    assert comparison["benchmark_periods"] == 2.0
    assert comparison["strategy_initial_equity"] == 105.0
    assert comparison["benchmark_initial_equity"] == 1_000.0
    assert comparison["benchmark_final_equity"] == pytest.approx(1_100.0)
    assert comparison["excess_total_return"] == pytest.approx(
        comparison["strategy_total_return"]
        - comparison["benchmark_total_return"]
    )
    assert not any("cagr" in key for key in comparison)


def test_prefers_net_returns_and_falls_back_to_gross(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "benchmark.csv"
    write_benchmark(path, ["2024-01-01", "2024-01-02", "2024-01-03"], [10, 11, 12])
    seen: list[pd.Series] = []

    def fake_summary(frame: pd.DataFrame, **kwargs: object) -> dict[str, float]:
        seen.append(frame["strategy_return"].copy())
        return {
            "initial_equity": 1.0,
            "final_equity": 1.0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "periods": 3.0,
        }

    monkeypatch.setattr(
        "el_psy_quant.backtesting.benchmarks.backtest_summary", fake_summary
    )
    compare_to_buy_and_hold_benchmark(make_result(), path)
    compare_to_buy_and_hold_benchmark(make_result(include_net=False), path)

    pd.testing.assert_series_equal(
        seen[0], make_result()["net_strategy_return"].rename("strategy_return")
    )
    pd.testing.assert_series_equal(seen[2], make_result(False)["strategy_return"])


def test_includes_annualized_metrics(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.csv"
    write_benchmark(path, ["2024-01-01", "2024-01-02", "2024-01-03"], [10, 11, 9])

    comparison = compare_to_buy_and_hold_benchmark(
        make_result(), path, periods_per_year=252
    )

    for key in (
        "strategy_cagr",
        "strategy_annualized_volatility",
        "strategy_sharpe_ratio",
        "benchmark_cagr",
        "benchmark_annualized_volatility",
        "benchmark_sharpe_ratio",
        "excess_cagr",
        "excess_sharpe_ratio",
    ):
        assert key in comparison


@pytest.mark.parametrize(
    ("result", "message"),
    [
        (pd.DataFrame(), "result must not be empty"),
        (pd.DataFrame({"strategy_return": [0.0]}), "'equity' column"),
        (pd.DataFrame({"equity": [1.0]}), "net_strategy_return.*strategy_return"),
    ],
)
def test_rejects_invalid_strategy_result(
    tmp_path: Path, result: pd.DataFrame, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        compare_to_buy_and_hold_benchmark(result, tmp_path / "unused.csv")


def test_rejects_fewer_than_two_aligned_rows(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.csv"
    write_benchmark(path, ["2024-01-03"], [10.0])

    with pytest.raises(ValueError, match="at least two aligned rows"):
        compare_to_buy_and_hold_benchmark(make_result(), path)


def test_rejects_non_positive_initial_capital(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="initial_capital must be positive"):
        compare_to_buy_and_hold_benchmark(
            make_result(), tmp_path / "unused.csv", initial_capital=0
        )


def test_propagates_benchmark_csv_validation_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    pd.DataFrame({"Date": ["2024-01-01"], "Close": [10.0]}).to_csv(
        path, index=False
    )

    with pytest.raises(ValueError, match="missing required columns"):
        compare_to_buy_and_hold_benchmark(make_result(), path)


def test_benchmark_helper_is_exported() -> None:
    from el_psy_quant import backtesting

    assert (
        backtesting.compare_to_buy_and_hold_benchmark
        is compare_to_buy_and_hold_benchmark
    )
