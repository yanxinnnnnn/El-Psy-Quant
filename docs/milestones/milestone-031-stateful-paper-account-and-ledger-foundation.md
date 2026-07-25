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
| S180 | Identity, Lifecycle, Decimal, and Evidence Reference Contracts | Complete |
| S181 | Immutable Cash Ledger and Account Event Foundation | Complete |
| S182 | Immutable Position Ledger and Aggregate Cost Basis Foundation | Complete |
| S183 | Snapshot, Reconciliation, and Projection Rebuild Foundation | Complete |
| S184 | Persistence, Migration, Concurrency, and Application Services | Implementation complete / pending Founder review |
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

## Sprint 181 result boundary

The second implementation slice reuses the Sprint 180 contracts and provides:

- an exact immutable cash-movement command with the six approved movement types;
- immutable creation, cash-movement, evidence-link, freeze, reactivate, and
  close events;
- one exact immutable cash entry for each financial event;
- deterministic command verification plus entry, event, and chain digests;
- contiguous per-account sequence and version authority;
- exact non-negative cash-only state with available cash equal to cash balance;
- pure command application; and
- fail-closed deterministic replay with no repair or caller-authored ending
  balance authority.

This cash-only state remains rebuildable but not persisted. Sprint 181 is
Complete after PR #359 merged.

## Sprint 182 result boundary

The third implementation slice reuses the single Sprint 181 event chain and
provides:

- one immutable normalized-symbol position-adjustment command;
- the exact `opening_balance`, `manual_correction`, `corporate_action`, and
  `other` categories;
- immutable position entries and the typed `position_adjustment_posted` event;
- exact ordered quantity and aggregate-cost-basis replay with long-only,
  non-negative, and zero-quantity/zero-cost-basis invariants;
- display-only average unit cost with explicit eight-place half-even rounding
  and a rounding indicator;
- one complete `PaperAccountLedgerState` containing exact cash, ordered current
  positions, lifecycle, evidence references, and head identity; and
- fail-closed replay of mixed cash, position, evidence, and lifecycle histories
  without changing valid Sprint 181 event digests.

This state remains pure and rebuildable in memory. It is not persisted and does
not add snapshot/reconciliation, API, Web, Demo, order/fill, market, execution,
or runtime behavior. Sprint 182 is Complete after PR #361 merged.

## Sprint 183 result boundary

The fourth implementation slice reuses full ledger replay and provides:

- canonical complete projections rebuilt only from immutable history;
- strict candidate validation and deterministic `current` or
  `reconciliation_required` verification without silent repair;
- the nine closed, ordered projection mismatch codes;
- immutable snapshot evidence at one exact replayed account head;
- immutable matched/mismatched reconciliation evidence with exact candidate and
  authoritative projection anchors; and
- canonical operation-command, projection, snapshot, and reconciliation
  digests with fail-closed scalar and nested-record validation.

These records are derived, non-authoritative, and in-memory only. They create no
event or posting and increment no account version. No persistence, migration,
filesystem artifact, API, Web, Demo, Docker, execution, or usable durable
account workflow was added in S183.

## Sprint 184 result boundary

The fifth implementation slice adds:

- the single additive `0007_paper_account_ledger` revision and exact schema
  verification;
- durable immutable account events and cash/position postings;
- database triggers preventing mutation/deletion of immutable authority;
- strict canonical JSON, decimal, timestamp, boolean, ordering, digest, and
  history reconstruction;
- durable creation, command, snapshot, and reconciliation idempotency;
- `BEGIN IMMEDIATE` plus guarded head compare-and-swap transactions;
- replaceable verified projection caches, explicit reconciliation, and explicit
  rebuild; and
- internal repository and application-service boundaries.

It adds no public API, Web, localization, Demo, Docker runtime acceptance,
filesystem evidence artifacts, market, order/fill, execution, or worker
behavior. Those boundaries remain S185–S187.

## Completion gate

M31 completes only when one account can be rebuilt and reconciled from verified
immutable ledger truth after restart, with no competing balance authority, and
the Founder has completed the approved Standard/Demo and bilingual runtime
acceptance.

## Preserved boundaries

- migration head is `0007_paper_account_ledger`;
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
docs/sprints/sprint-181-immutable-cash-ledger-and-account-event-foundation.md
docs/sprints/sprint-182-immutable-position-ledger-and-aggregate-cost-basis-foundation.md
docs/sprints/sprint-183-account-snapshot-reconciliation-and-projection-rebuild-foundation.md
docs/sprints/sprint-184-durable-paper-account-persistence-migration-concurrency-and-application-service-foundation.md
```
