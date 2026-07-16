# Founder Workflow

The Founder workflow turns a strategy idea into a reviewable chain of evidence.
It does not turn that evidence into an automatic decision.

In Demo Workspace mode, Overview supplies one coherent versioned journey using
exact backend-provided references. In a standard workspace, choose and verify
each real record yourself; generic pages do not claim that unrelated records
belong to one chain.

```text
Strategy
  ↓
Research Evidence
  ↓
Governance Evidence
  ↓
Paper Run
  ↓
Portfolio Result
  ↓
Comparison
  ↓
Lifecycle Review
  ↓
Human Decision Evidence
```

## 1. Inspect the Strategy

Open **Strategies and Research**, choose **Strategies**, and inspect a strategy
definition. Confirm its exact name, description, parameter types, required
fields, and defaults.

The definition is read-only. The page does not run, edit, rank, or recommend the
strategy.

## 2. Review Research Evidence

Open **Research runs** and choose the saved run that matches your intended
strategy and experiment. Check:

- experiment and run identity;
- data source and symbols;
- strategy parameters and evaluation settings;
- saved per-symbol return, drawdown, volatility, and risk-adjusted metrics; and
- artifact references and schema information.

Metrics are displayed from saved evidence. Look for weak assumptions, missing
values, concentration, and inconsistent behavior across symbols. Historical
research does not guarantee future or paper performance.

## 3. Inspect Governance Evidence

Open **Governance and Reports** and select the relevant evidence manifest.
Confirm its type, ID, creation metadata, description, and ordered reference
groups.

Strategy decision manifests separate summary and decision-record references.
Report artifact manifests show report metadata and references. Strategy review
workflow manifests separate source snapshots, transition proposals, and human
transition records.

References are identifiers, not links. The workspace does not resolve them,
judge completeness, infer approval, or render the referenced report. Carry the
exact type and ID into later review steps only after you have verified what each
reference represents.

## 4. Create and Run a Paper Job

Open **Paper Runs**, choose **Submit queued job**, and enter the complete paper
command fields shown by the form. Submission creates a durable `queued` job; it
does not run it.

On the job detail page, inspect the identity and then choose **Run** only when
the request is ready. Confirm the action. An accepted Run response means the
request was scheduled for local processing, not that it completed. Use
**Refresh status** manually until the backend reports the later state.

Paper execution is local and does not send orders to a broker or market.

## 5. Interpret the Portfolio Result

When the job is `succeeded` and **Result available** is **Yes**, open its
Portfolio Record. Review the identity and provenance first, followed by account
cash snapshots, session summary, positions, position changes, orders, fills,
and the separate result audit.

Account cash is not total marked-to-market equity. The workspace has no market
prices for open positions and does not calculate valuation, profit, return, or
exposure from a paper result. Treat cash changes and counts as backend-supplied
facts, not as an investment conclusion.

## 6. Compare Multiple Paper Runs

Open **Comparisons**, select two to four distinct succeeded jobs with available
results, and choose **Compare selected results**. Review the side-by-side cash,
session, audit, position, and position-change facts.

The comparison does not align trades, calculate cross-run differences, rank
runs, or choose a winner. Open each linked Portfolio Record for the full orders
and fills, then document your own conclusion and its assumptions.

## 7. Prepare a Lifecycle Proposal

Open **Lifecycle Review** only after the evidence chain is ready. Enter an
explicit source snapshot, target state, rationale, and evidence references.
Choose **Create non-executing proposal** and inspect the normalized response.

The proposal requests human review. It is not approval and does not change a
lifecycle state.

In Demo Workspace mode, **Load demo lifecycle example** fills these command
inputs from the backend descriptor. Review every value before submitting. The
action does not submit, approve, or apply a transition.

## 8. Record Human Decision Evidence

Using the normalized proposal, enter a transition record ID, an explicit human
outcome, reviewer details, rationale, notes, and warnings. Include a resulting
snapshot only when the selected outcome requires one. Choose **Record human
review evidence** and inspect the response and in-session timeline.

The response is governance evidence visible in the current browser session. The
workspace does not persist a review history, apply the transition, declare a
globally current state, allocate capital, or start another workflow. The human
reviewer remains responsible for the decision and for any separately governed
follow-up.
