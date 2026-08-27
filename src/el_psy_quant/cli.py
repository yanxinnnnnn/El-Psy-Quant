"""Minimal command-line entrypoint for local configured experiments."""

import argparse
import json
import shutil
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from el_psy_quant.backtesting import summarize_multi_symbol_results
from el_psy_quant.config import load_experiment_config
from el_psy_quant.data import (
    load_daily_prices_csvs,
    read_daily_prices_caches,
    validate_daily_prices_by_symbol,
)
from el_psy_quant.demo_workspace import (
    DemoWorkspaceError,
    install_demo_workspace,
    resolve_workspace_mode,
)
from el_psy_quant.local_workspace import (
    LocalWorkspaceError,
    format_verification_success,
    start_local_backend,
    verify_local_workspace,
)
from el_psy_quant.outputs import create_experiment_output_layout
from el_psy_quant.application import PaperExecutionApplicationService
from el_psy_quant.application.paper_runtime import (
    PaperRuntimeOwnershipBusyError,
    PaperRuntimeOwnershipService,
    PaperRuntimeRecoveryService,
    PaperRuntimeRunnerService,
)
from el_psy_quant.persistence import (
    PaperRuntimeNotFoundError,
    PaperRuntimePersistenceCorruptionError,
    PaperRuntimeStorageBusyError,
    PaperRuntimeStorageFailureError,
    create_product_database_engine,
    create_product_session_factory,
    resolve_product_database_config,
)
from el_psy_quant.persistence.schema import (
    ProductSchemaVerificationError,
    verify_product_schema,
)
from el_psy_quant.strategies import resolve_strategy


@dataclass(frozen=True)
class PaperRuntimeProcessResult:
    """Bounded process outcome without exposing internal runtime payloads."""

    runtime_id: str
    recovery_outcome: str
    runner_outcome: str | None
    fencing_token: int
    iterations: int


def run_paper_runtime_process(
    *,
    database_path: str | Path,
    runtime_id: str,
    owner_id: str,
    lease_seconds: int = 30,
    iteration_budget: int | None = None,
) -> PaperRuntimeProcessResult:
    """Compose S222 recovery then S221 runner over one shared session factory."""

    if type(lease_seconds) is not int or lease_seconds <= 0:
        raise ValueError("lease_seconds must be strictly positive")
    if iteration_budget is not None and (
        type(iteration_budget) is not int or iteration_budget <= 0
    ):
        raise ValueError("iteration_budget must be strictly positive")
    config = resolve_product_database_config(database_path=database_path)
    verify_product_schema(config.database_path)
    engine = create_product_database_engine(config=config)
    try:
        session_factory = create_product_session_factory(engine=engine)
        execution = PaperExecutionApplicationService(session_factory=session_factory)
        ownership = PaperRuntimeOwnershipService(
            session_factory=session_factory,
            lease_duration=timedelta(seconds=lease_seconds),
        )
        recovery = PaperRuntimeRecoveryService(
            session_factory=session_factory,
            execution_service=execution,
            ownership_service=ownership,
        )
        runner = PaperRuntimeRunnerService(
            session_factory=session_factory,
            execution_service=execution,
            ownership_service=ownership,
        )
        recovered = recovery.recover_runtime(
            runtime_id=runtime_id,
            recovery_owner_id=owner_id,
        )
        runner_outcome = None
        iterations = 0
        runtime = recovered.runtime
        if recovered.outcome == "runnable":
            if runtime.owner_id != owner_id:
                raise PaperRuntimePersistenceCorruptionError()
            loop = runner.run_claimed_runtime(
                runtime_id=runtime.runtime_id,
                owner_id=owner_id,
                fencing_token=runtime.fencing_token,
                iteration_budget=iteration_budget,
            )
            runner_outcome = loop.outcome
            iterations = loop.iterations
            runtime = loop.runtime
        return PaperRuntimeProcessResult(
            runtime_id=runtime.runtime_id,
            recovery_outcome=recovered.outcome,
            runner_outcome=runner_outcome,
            fencing_token=runtime.fencing_token,
            iterations=iterations,
        )
    finally:
        engine.dispose()


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


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

    validate_daily_prices_by_symbol(prices_by_symbol)
    parameters = config.parameters
    parameter_mapping = {
        "fast_window": parameters.fast_window,
        "slow_window": parameters.slow_window,
        "initial_capital": parameters.initial_capital,
        "transaction_cost_rate": parameters.transaction_cost_rate,
        "slippage_rate": parameters.slippage_rate,
    }
    strategy = resolve_strategy(config.strategy)
    results_by_symbol = {
        symbol: strategy.run(prices, parameter_mapping)
        for symbol, prices in prices_by_symbol.items()
    }
    summary = summarize_multi_symbol_results(
        results_by_symbol,
        periods_per_year=config.evaluation.periods_per_year,
        annual_risk_free_rate=config.evaluation.annual_risk_free_rate,
    )

    summary_path = layout.results_dir / "summary.csv"
    summary_artifact = summary_path.relative_to(layout.run_dir).as_posix()
    shutil.copyfile(config_path, layout.config_path)
    metadata = {
        "experiment_name": config.name,
        "strategy": config.strategy,
        "data_source": config.data.source,
        "run_id": layout.run_dir.name,
        "summary_path": summary_artifact,
    }
    layout.metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    summary.to_csv(summary_path, index=False)
    metrics = {
        "schema_version": 1,
        "run_id": layout.run_dir.name,
        "source_artifact": summary_artifact,
        "metrics": summary.to_dict(orient="records"),
    }
    layout.metrics_path.write_text(
        json.dumps(metrics, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "experiment_name": config.name,
        "strategy": config.strategy,
        "run_id": layout.run_dir.name,
        "data": {
            "source": config.data.source,
            "symbols": list(prices_by_symbol),
        },
        "parameters": {
            "fast_window": parameters.fast_window,
            "slow_window": parameters.slow_window,
            "initial_capital": parameters.initial_capital,
            "transaction_cost_rate": parameters.transaction_cost_rate,
            "slippage_rate": parameters.slippage_rate,
        },
        "evaluation": {
            "periods_per_year": config.evaluation.periods_per_year,
            "annual_risk_free_rate": config.evaluation.annual_risk_free_rate,
        },
        "artifacts": {
            "config": layout.config_path.relative_to(layout.run_dir).as_posix(),
            "metadata": layout.metadata_path.relative_to(
                layout.run_dir
            ).as_posix(),
            "summary": summary_artifact,
            "metrics": layout.metrics_path.relative_to(
                layout.run_dir
            ).as_posix(),
            "logs_dir": layout.logs_dir.relative_to(layout.run_dir).as_posix(),
        },
    }
    layout.manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
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
    demo_parser = subparsers.add_parser(
        "install-demo-workspace",
        help="install the validated demo dataset into isolated demo storage",
    )
    demo_parser.add_argument("--source-root", type=Path, required=True)
    demo_parser.add_argument("--workspace-root", type=Path, required=True)
    demo_parser.add_argument("--alembic-config", type=Path, required=True)
    verify_parser = subparsers.add_parser(
        "verify-local-workspace",
        help="read-only verification of one explicit Standard or Demo workspace",
    )
    verify_parser.add_argument(
        "--mode",
        choices=("standard", "demo"),
        required=True,
    )
    verify_parser.add_argument("--workspace-root", type=Path, required=True)
    startup_parser = subparsers.add_parser(
        "start-local-backend",
        help="prepare, verify, and start the local container backend",
    )
    startup_parser.add_argument(
        "--mode",
        choices=("standard", "demo"),
        required=True,
    )
    startup_parser.add_argument("--workspace-root", type=Path, required=True)
    startup_parser.add_argument("--alembic-config", type=Path, required=True)
    startup_parser.add_argument("--demo-source-root", type=Path)
    runtime_parser = subparsers.add_parser(
        "run-paper-runtime",
        help="recover then run one durable Paper Runtime",
    )
    runtime_parser.add_argument("--database-path", type=Path, required=True)
    runtime_parser.add_argument("--runtime-id", required=True)
    runtime_parser.add_argument("--owner-id", required=True)
    runtime_parser.add_argument("--lease-seconds", type=_positive_int, default=30)
    runtime_parser.add_argument("--iteration-budget", type=_positive_int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""
    args = _build_parser().parse_args(argv)
    if args.command == "run-paper-runtime":
        try:
            result = run_paper_runtime_process(
                database_path=args.database_path,
                runtime_id=args.runtime_id,
                owner_id=args.owner_id,
                lease_seconds=args.lease_seconds,
                iteration_budget=args.iteration_budget,
            )
        except ProductSchemaVerificationError:
            print("error: paper runtime schema is incompatible", file=sys.stderr)
            return 1
        except PaperRuntimeNotFoundError:
            print("error: paper runtime was not found", file=sys.stderr)
            return 1
        except PaperRuntimeOwnershipBusyError:
            print("error: paper runtime has an active foreign owner", file=sys.stderr)
            return 1
        except PaperRuntimeStorageBusyError:
            print("error: paper runtime storage is temporarily unavailable", file=sys.stderr)
            return 1
        except (
            PaperRuntimePersistenceCorruptionError,
            PaperRuntimeStorageFailureError,
        ):
            print("error: paper runtime authority is unavailable", file=sys.stderr)
            return 1
        except (OSError, RuntimeError, TypeError, ValueError):
            print("error: paper runtime process input is invalid", file=sys.stderr)
            return 1
        runner_outcome = result.runner_outcome or "not_run"
        print(
            f"runtime_id={result.runtime_id} recovery={result.recovery_outcome} "
            f"runner={runner_outcome} fence={result.fencing_token} "
            f"iterations={result.iterations}"
        )
        return 0
    if args.command == "verify-local-workspace":
        try:
            result = verify_local_workspace(
                mode=args.mode,
                workspace_root=args.workspace_root,
            )
        except LocalWorkspaceError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        print(format_verification_success(result))
        return 0
    if args.command == "start-local-backend":
        try:
            start_local_backend(
                mode=args.mode,
                workspace_root=args.workspace_root,
                alembic_config_path=args.alembic_config,
                demo_source_root=args.demo_source_root,
            )
        except LocalWorkspaceError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        return 0
    if args.command == "install-demo-workspace":
        try:
            result = install_demo_workspace(
                source_root=args.source_root,
                workspace_root=args.workspace_root,
                workspace_mode=resolve_workspace_mode(),
                alembic_config_path=args.alembic_config,
            )
        except (DemoWorkspaceError, OSError, ValueError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        status = "already installed" if result.already_installed else "installed"
        print(
            f"{result.dataset_id} v{result.dataset_version} {status} "
            f"at {result.workspace_root}"
        )
        return 0

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
