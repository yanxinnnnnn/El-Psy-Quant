"""Minimal command-line entrypoint for local configured experiments."""

import argparse
import json
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from el_psy_quant.backtesting import (
    moving_average_crossover_multi_symbol,
    summarize_multi_symbol_results,
)
from el_psy_quant.config import load_experiment_config
from el_psy_quant.data import load_daily_prices_csvs, read_daily_prices_caches
from el_psy_quant.outputs import create_experiment_output_layout


def run_configured_experiment(
    config_path: str | Path,
    output_root: str | Path,
    run_id: str | None = None,
) -> Path:
    """Run one local configured experiment and write its minimal artifacts."""
    config_path = Path(config_path)
    config = load_experiment_config(config_path)
    layout = create_experiment_output_layout(
        output_root,
        config.name,
        run_id=run_id,
    )

    if config.data.source == "csv":
        assert config.data.paths is not None
        prices_by_symbol = load_daily_prices_csvs(config.data.paths)
    else:
        assert config.data.cache_dir is not None
        prices_by_symbol = read_daily_prices_caches(
            config.data.cache_dir,
            config.data.symbols,
        )

    parameters = config.parameters
    results_by_symbol = moving_average_crossover_multi_symbol(
        prices_by_symbol,
        fast_window=parameters.fast_window,
        slow_window=parameters.slow_window,
        initial_capital=parameters.initial_capital,
        transaction_cost_rate=parameters.transaction_cost_rate,
        slippage_rate=parameters.slippage_rate,
    )
    summary = summarize_multi_symbol_results(
        results_by_symbol,
        periods_per_year=config.evaluation.periods_per_year,
        annual_risk_free_rate=config.evaluation.annual_risk_free_rate,
    )

    summary_path = layout.results_dir / "summary.csv"
    shutil.copyfile(config_path, layout.config_path)
    metadata = {
        "experiment_name": config.name,
        "strategy": config.strategy,
        "data_source": config.data.source,
        "run_id": layout.run_dir.name,
        "summary_path": summary_path.relative_to(layout.run_dir).as_posix(),
    }
    layout.metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    summary.to_csv(summary_path, index=False)
    return layout.run_dir


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="el-psy-quant")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser(
        "run",
        help="run one local YAML-configured experiment",
    )
    run_parser.add_argument("config_path", type=Path)
    run_parser.add_argument("--output-root", type=Path, required=True)
    run_parser.add_argument("--run-id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""
    args = _build_parser().parse_args(argv)
    try:
        run_dir = run_configured_experiment(
            args.config_path,
            args.output_root,
            run_id=args.run_id,
        )
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
