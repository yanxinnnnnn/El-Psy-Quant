# Milestone 31 — Stateful Paper Account and Ledger Foundation

## Status

**In Progress.** GitHub Issue #355 is the authoritative architecture source.

## Objective

Establish a durable local Paper Account whose lifecycle, cash, positions,
aggregate cost basis, immutable history, snapshots, and reconciliation derive
from one exact ordered ledger authority across restarts.

M31 keeps legacy Paper evidence, M30 portfolio-review governance, lifecycle
governance, Paper Jobs, and future account/ledger truth as separate authorities.

## Approved sprint sequence

| Sprint | Deliverable | Status |
|---:|---|---|
| S179 | Milestone 31 Architecture and Planning | Complete |
| S180 | Identity, Lifecycle, Decimal, and Evidence Reference Contracts | Implementation complete / pending Founder review |
| S181 | Immutable Cash Ledger and Account Event Foundation | Planned |
| S182 | Immutable Position Ledger and Aggregate Cost Basis Foundation | Planned |
| S183 | Snapshot, Reconciliation, and Projection Rebuild Foundation | Planned |
| S184 | Persistence, Migration, Concurrency, and Application Services | Planned |
| S185 | Versioned API, Errors, and Audit Surface | Planned |
| S186 | Bilingual Founder Paper Account Web Workspace | Planned |
| S187 | Integration, Demo, Upgrade, Recovery, and Acceptance Hardening | Planned |
| S188 | Milestone 31 Closeout and Next-Milestone Handoff | Planned |

Dependencies are strict. Later sprint behavior must not be pulled into an
earlier sprint.

## Sprint 180 result boundary

The first implementation slice provides only pure immutable contracts:

- exact canonical `Decimal` money and quantity values;
- account creation identity and compact references;
- the exact `active / frozen / closed` vocabulary;
- explicit ledger-derived close-eligibility facts;
- pure lifecycle transition validation;
- immutable create, freeze, reactivate, close, and M30 evidence-link commands;
- deterministic canonical JSON and SHA-256 command digests; and
- a bounded governance reference created only from a genuine approved M30
  `PortfolioReviewDecisionArtifact`.

This slice does not produce a usable account balance, ledger event, posting,
projection, snapshot, reconciliation, database record, API, or Web workflow.

## Completion gate

M31 completes only when one account can be rebuilt and reconciled from verified
immutable ledger truth after restart, with no competing balance authority, and
the Founder has completed the approved Standard/Demo and bilingual runtime
acceptance.

## Preserved boundaries

- migration head remains `0006_portfolio_reviews` until the S184 migration;
- Standard and Demo storage remain isolated;
- M30 approval is governance evidence, not account or capital authority;
- M30 scenario weights are assumptions, not holdings;
- legacy `el_psy_quant.paper` objects remain evidence contracts only;
- no order/fill runtime or reservation authority exists in M31; and
- M32–M36 retain no sprint ranges.

M34 remains the first genuine market/strategy-driven Paper Trading gate. M36
remains the continuous multi-day Paper Trading gate.

## Records

```text
docs/architecture/stateful-paper-account-and-ledger.md
docs/sprints/sprint-179-milestone-31-architecture-and-planning.md
docs/sprints/sprint-180-paper-account-identity-lifecycle-decimal-and-evidence-reference-contract-foundation.md
```
