# Sprint 42 — Milestone 10 Planning

## Objective

Plan Milestone 10 after completing the project quality foundation.

## CTO Decision

Milestone 10 will be:

```text
Experiment Artifact & Comparison Foundation
```

## Why This Milestone Comes Next

Milestone 8 made configured local experiments runnable. Milestone 9 made future changes easier to trust through CI, repository hygiene, and a local quality gate.

The next weakness is not strategy quantity. The next weakness is that experiment outputs still need stronger artifact discipline.

A research platform should make it easy to answer:

```text
What exactly ran?
What config produced this result?
What metrics came out?
Where are the artifacts?
How does this run compare with another run?
```

Milestone 10 should answer those questions before the project adds more strategies.

## Product Goal

Experiment runs should produce stable, inspectable artifacts that can be compared across runs without relying on memory, ad hoc file inspection, or handwritten notes.

## Planned Sprint Sequence

| Sprint | Status | Goal | Main Deliverable | Guardrail |
|---:|---|---|---|---|
| S42 | Complete | Plan Milestone 10. | Milestone 10 scope and sprint sequence. | No implementation during planning. |
| S43 | Planned | Add experiment run manifest. | Stable `manifest.json` describing a run. | No database or dashboard. |
| S44 | Planned | Add metrics artifact. | Stable machine-readable metrics output. | No new metrics unless already available. |
| S45 | Planned | Add experiment comparison. | Compare saved experiment runs from local artifacts. | No strategy optimization engine. |
| S46 | Planned | Close milestone. | Milestone 10 documentation refresh. | Keep artifact rules simple. |

## Milestone 10 Exit Criteria

Milestone 10 is complete when local configured experiment runs can leave behind enough structured artifacts to support basic comparison across runs.

At minimum, a reviewer should be able to inspect local run folders and understand:

- run identity
- experiment name
- run timestamp or run id
- input config location
- output artifact paths
- summary or metrics artifact location
- basic comparison between two or more runs

## Explicit Non-Goals

Milestone 10 will not add:

- new trading strategies
- alpha research claims
- a database
- a dashboard
- cloud storage
- paper trading
- broker integration
- live data automation
- a reporting framework
- a strategy optimization engine

## Engineering Principle

```text
Experiments that cannot be inspected later are not research assets.
```

## Next Sprint

The next implementation sprint is:

```text
Sprint 43 — Experiment Run Manifest Foundation
```

Sprint 43 should add a small manifest artifact to the existing local experiment output layout. It should not redesign the CLI or introduce storage infrastructure.
