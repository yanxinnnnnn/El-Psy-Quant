# Sprint 1 — Bootstrap & Foundation

## Objective

Bootstrap El-Psy-Quant as a real engineering project and implement the first market data capability.

This sprint should produce a repository that Codex and future AI agents can understand and safely extend.

## Product Goal

As the founder, I want a clean Python project foundation so that future quant research features can be implemented through small, reviewable pull requests.

## Technical Direction

Use a modern Python project layout:

```text
El-Psy-Quant/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── src/
│   └── el_psy_quant/
│       ├── __init__.py
│       └── data/
│           ├── __init__.py
│           └── providers.py
├── tests/
│   └── test_project_import.py
└── docs/
    └── sprints/
        └── sprint-001-bootstrap-foundation.md
```

## Implementation Scope

### Must Have

- Create a Python package using `src/` layout.
- Add `pyproject.toml`.
- Use `uv` as the intended package manager.
- Add development tools:
  - `pytest`
  - `ruff`
- Add a minimal import test.
- Add a first market data provider interface.
- Add a simple Yahoo Finance provider skeleton, but do not overbuild it.

### Nice to Have

- Support saving downloaded data to `data/raw/` as CSV or Parquet.
- Add basic logging.
- Add a short usage example in README.

### Out of Scope

- No trading strategy yet.
- No backtesting engine yet.
- No broker integration.
- No real-money trading.
- No ML/AI strategy generation.

## Suggested Data Provider Design

Start simple.

```python
from typing import Protocol
import pandas as pd

class MarketDataProvider(Protocol):
    def download_daily_prices(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        ...
```

A concrete provider can later use `yfinance`.

The returned DataFrame should include daily OHLCV-style columns where available:

- Open
- High
- Low
- Close
- Adj Close
- Volume

## Acceptance Criteria

- `uv sync` can install the project dependencies.
- `uv run pytest` passes.
- `uv run ruff check .` passes.
- `uv run python -c "import el_psy_quant"` works.
- README explains how to install and run the basic checks.
- The implementation stays small and reviewable.

## Codex Instruction

When implementing this sprint:

1. Read `AGENTS.md` first.
2. Implement only the sprint scope.
3. Keep the first PR small.
4. Do not introduce strategy, backtesting, broker, dashboard, or cloud features yet.
5. Prefer clear code over clever abstractions.
6. Add tests for importability and any pure logic.

## Review Notes

The founder should review:

- Whether the project can be installed locally.
- Whether file names and package names are clear.
- Whether Codex added unnecessary complexity.
- Whether network-dependent logic is isolated from tests.