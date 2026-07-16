# Research

The Research area presents saved research-run manifests and their saved
per-symbol metrics. It is an evidence-inspection workspace, not a research
execution tool.

## Find the Intended Run

Open **Strategies and Research**, select **Research runs**, and match the run by
experiment name, experiment slug, run ID, strategy, data source, and symbols.
Open **Inspect saved result** for the exact run.

On the detail page, review:

- manifest and metrics schema versions;
- data source and symbol coverage;
- strategy parameters, including capital, costs, and slippage assumptions;
- evaluation settings, including periods per year and risk-free rate;
- saved artifact references; and
- every saved per-symbol metric row.

## Interpret Saved Metrics

The page may show initial and final equity, total return, maximum drawdown,
period count, CAGR, annualized volatility, and Sharpe ratio. These are saved
research values. The browser formats them for display but does not recompute,
aggregate, reconcile, or rank them.

Review metrics together. A higher return does not remove drawdown, volatility,
cost, data-quality, or sample-length risk. A missing annualized value appears as
**Not available** and should not be silently replaced with an estimate.

## Artifact References

Artifact references are read-only text. They identify configured research
outputs but are not download links and do not give the browser access to local
files. The current view does not reconstruct an equity curve or provide charts.

## Empty and Error States

An empty state means the configured research source was reached and contained no
supported runs. An unavailable or invalid state means the evidence could not be
read safely. Retry if appropriate, and do not continue as though missing
evidence had been reviewed.
