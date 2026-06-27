# Sprint 10 — Minimal Local Research Example

## Objective

Add the first minimal local research example.

Sprint 9 added a compact backtest summary layer. Sprint 10 should show how a user can run the current research pipeline end to end from a local script, without adding new platform capabilities or relying on live market data.

## Product Goal

As the founder, I want a simple runnable example so that a new contributor can understand the complete El-Psy-Quant workflow in one file.

The example should demonstrate:

```text
sample close prices
  -> moving_average_crossover_pipeline
  -> backtest_summary
  -> printed summary
```

## Technical Direction

Create an examples directory:

```text
examples/
└── minimal_research_example.py

tests/
└── test_examples.py
```

The example should be deterministic and network-free.

It should not fetch Yahoo Finance data yet. Live-data examples will come later after local reproducibility is stronger.

## Implementation Scope

### Must Have

Add:

```text
examples/minimal_research_example.py
```

The script should:

- Create a small deterministic `pd.Series` of close prices.
- Run `moving_average_crossover_pipeline`.
- Run `backtest_summary`.
- Print the final few rows of the result DataFrame.
- Print the summary dictionary in a readable way.
- Have a `main()` function.
- Use `if __name__ == "__main__": main()`.
- Avoid network calls.
- Avoid file output.
- Avoid charts.

### Nice to Have

- Add a short module docstring explaining that this is a deterministic local example.
- Use a slightly longer sample price series so the moving averages and signals are meaningful.
- Keep printed output compact.

### README Update

Add a short section explaining how to run the example:

```bash
uv run python examples/minimal_research_example.py
```

### Tests

Add tests covering:

- The example module can be imported.
- `main()` runs without raising.
- The example does not call Yahoo Finance or any market data provider.
- The example prints output containing at least:
  - `summary`
  - `total_return`
  - `max_drawdown`

Use pytest `capsys` and `monkeypatch` where useful.

## Out of Scope

- No live Yahoo Finance example.
- No CLI argument parsing.
- No charts.
- No CSV files.
- No file export.
- No notebooks.
- No dashboards.
- No new indicators.
- No new strategies.
- No new metrics.
- No backtesting engine changes.
- No transaction costs or slippage.
- No broker integration.

## Acceptance Criteria

- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python examples/minimal_research_example.py` works.
- README includes the example run command.
- The example is deterministic and network-free.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only Sprint 10 scope.
3. Do not introduce live data fetching, CLI parsing, charts, notebooks, dashboards, CSV files, file exports, new indicators, new strategies, new metrics, backtesting engine changes, transaction costs, slippage, cloud features, or broker integration.
4. Keep the example deterministic and easy to read.
5. Do not use live market data in tests.
6. Keep the PR small and reviewable.

## Review Notes

The founder should review:

- Whether the example is easy to understand for a beginner.
- Whether it demonstrates the current platform flow clearly.
- Whether it stays deterministic and network-free.
- Whether Codex avoided turning the example into a CLI/app/framework.