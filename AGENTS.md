# AGENTS.md

This file defines the shared context for AI agents working on El-Psy-Quant.

## Project Identity

El-Psy-Quant is an AI-native quantitative research and trading platform.

The project is built like a startup product, not a one-off learning script.

## Mission

Build a production-ready platform that can ingest market data, research strategies, run backtests, generate reports, and eventually support paper trading and small-scale live trading.

## Operating Model

- The human founder makes final decisions.
- AI agents may implement code, tests, and documentation.
- AI-generated code must be reviewable, tested, and simple.
- Do not optimize for cleverness. Optimize for correctness and maintainability.

## Engineering Principles

- Use Python.
- Prefer modern Python packaging and tooling.
- Prefer `uv` for dependency management unless the founder decides otherwise.
- Use a `src/` layout.
- Use `pytest` for testing.
- Use `ruff` for formatting and linting.
- Use type hints for public functions.
- Keep modules small and composable.
- Avoid premature abstraction.
- Avoid hidden network calls in tests.
- Keep financial calculations explicit and well documented.

## Quant Principles

- Never claim a strategy is profitable without evidence.
- Avoid look-ahead bias.
- Avoid survivorship bias where possible.
- Always distinguish research code, backtesting code, and execution code.
- Prefer reproducible experiments.
- Risk metrics matter as much as return metrics.

## Definition of Done

A task is done only when:

- The code runs locally.
- Tests are included where appropriate.
- README or docs are updated when behavior changes.
- Assumptions and limitations are documented.
- The implementation is simple enough for a human reviewer to understand.

## Current Focus

Sprint 1 focuses on project bootstrap and the first market data capability.