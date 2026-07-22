# Sprint 176 — Portfolio Review Workflow Integration, Demo, and Acceptance Hardening

## Status

**Complete; Founder Standard/Demo runtime acceptance remains blocked on Sprint
177 recovery.**

Sprints 169–176 are Complete. Milestone 30 remains In Progress. Founder Standard
startup exposed the installed-wheel Alembic resource defect recorded in Sprint
177. Sprint 178 — Milestone 30 Closeout and M31 Handoff is next only after the
recovery fix is merged and complete Founder acceptance succeeds. The single
migration head remains `0006_portfolio_reviews`.

## Delivered boundary

The existing four portfolio-review routes and their request/response payloads
remain unchanged. The create workspace now composes existing public reads only:

- an explicitly selected research run may copy its exact `strategy`, optional
  `experiment_name`, declared symbol order, and one opaque `research_run`
  reference `<experiment_slug>/<run_id>`;
- explicitly selected compatible evidence-manifest references copy type, ID,
  label, and description verbatim and in backend grouping/order;
- unsupported references remain visible and non-importable; and
- exact duplicate type/ID pairs are refused within a component.

Research summary metrics, Paper Job comparisons, labels, and lifecycle form
state are not aligned-return authority. There is no persisted public
`paper_comparison_summary` discovery contract. Aligned returns, static weights,
scenarios, rationales, audit fields, and proposed-component selection remain
explicit Founder input. The browser does not calculate portfolio evidence.

## Demo v2

Demo source schema, descriptor schema, and dataset version are 2. The isolated
installer validates the exact nested create request and referenced public Demo
identities before target mutation, then uses existing domain/application
authority to seed `demo-portfolio-review-001` as `awaiting_decision`. Exact
replay validates the seeded authority, preserves a valid later human decision,
and leaves extra Founder-created Demo reviews untouched.

The Demo create action is prefill only. It is visible only in Demo mode, requires
explicit replace-draft confirmation, keeps the supplied idempotency key editable,
and never auto-loads, submits, or selects/records a decision. An installed Demo
v1 source conflicts with v2 by design; only the Founder may reset the disposable
Demo volume. Standard is never seeded.

Standard and Demo keep separate Compose projects, databases, artifact roots,
and named volumes. A Demo reset must not touch Standard storage.

## Read-only and audit hardening

The bilingual verifier reads both portfolio-review routes, the list, descriptor
v2, and the exact seeded detail without issuing create/decision commands.
Portfolio command events are limited to request/command identity plus
`review_id`, `decision_id`, `command_outcome`, and
`human_decision_outcome`. They exclude credentials, headers/cookies,
idempotency keys, bodies, returns, weights, financial values, artifacts, paths,
SQL, exceptions, and tracebacks.

An `approved`, `rejected`, or `deferred` decision is immutable governance
evidence only. It does not mutate lifecycle, allocate capital, create an account,
place an order, or execute. M31 account and ledger truth remains deferred.

## Verification ownership

Codex owns deterministic repository checks, Alembic-head inspection, and static
Compose rendering. Codex does not build/pull images, start containers, run
container smoke, remove volumes, reset Demo, or perform browser runtime
acceptance. The Founder owns those operations and the final merge decision.

## Founder-owned Standard acceptance

```text
build/start Standard with existing local procedure
  -> migration reaches 0006_portfolio_reviews
  -> Demo descriptor remains not configured
  -> no bundled portfolio review is seeded
  -> research/evidence integration is explicit
  -> manual builder remains usable when configured sources are empty/unavailable
  -> stop Standard without deleting its volume
```

## Founder-owned Demo acceptance

```text
explicitly reset disposable Demo v1 volume when required
  -> build/start Demo using isolated Demo project/volume
  -> descriptor v2 is visible and clearly labeled
  -> seeded review appears in list/detail as exact synthetic evidence
  -> load Demo create example explicitly; confirm no auto-submit
  -> submit and observe exact replay/authoritative detail
  -> record one explicit approved/rejected/deferred decision
  -> restart Demo and confirm the valid decision persists
  -> return to Standard and confirm Standard data is unchanged
```

## Known limitations and handoff

There is no automatic source/candidate/weight/outcome selection, return repair,
normalization, recommendation, persisted comparison summary, lifecycle bridge,
Paper Account, ledger, market clock, order/fill simulation, worker, broker, QMT,
MiniQMT, or live behavior. Sprint 178 may close M30 only after Founder acceptance;
it hands immutable review evidence to M31 without handing off account truth.
