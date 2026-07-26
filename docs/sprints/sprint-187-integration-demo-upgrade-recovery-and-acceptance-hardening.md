# Sprint 187 — Integration, Demo, Upgrade, Recovery, and Acceptance Hardening

## Authority

GitHub Issue #370 is the authoritative Sprint 187 implementation
specification. Issue #355 remains the Milestone 31 architecture authority.
Sprints 180–186 retain their domain, persistence, replay, projection, API, and
Web authority boundaries.

## Status

**Implementation complete; Founder review, Docker runtime acceptance, browser
acceptance, and merge remain pending.**

## Result

Sprint 187 hardens the integrated M31 path without adding financial authority.
Demo source schema, dataset, and descriptor are version 3. An earlier installed
Demo dataset conflicts deliberately and requires the documented Founder-owned
Demo-only reset.

Demo v3 creates one synthetic Paper Account only through
`PaperAccountApplicationService`:

```text
account creation
  -> explicit cash deposit
  -> explicit opening-position adjustment
  -> freeze
  -> reactivate
  -> immutable snapshot
  -> matched reconciliation
```

Server-owned deterministic IDs and UTC timestamps make installation
reproducible. Exact restart replay reissues the same creation, command, snapshot,
and reconciliation intents through their approved idempotency boundaries.
Ledger events/postings remain financial authority. Deterministic ledger replay
remains state authority. The persisted projection remains a replaceable cache,
and snapshot/reconciliation rows remain immutable derived evidence.

## Fail-closed verification

Installation and restart validation:

- reconstruct and exactly replay all five immutable events and postings;
- compare replayed state with the expected synthetic cash and position facts;
- rebuild the projection from replay and compare it with the strictly loaded
  persisted projection;
- reopen and validate the immutable snapshot and its embedded projection;
- reopen and validate the matched reconciliation and both projection digests;
  and
- require the exact descriptor and dataset digest.

Projection or ledger corruption is refused. Validation does not call projection
rebuild, replace a cache row, edit a ledger row, reseed a conflicting dataset,
or repair a workspace.

The bilingual read-only MVP verifier now reads the descriptor-provided account
detail and bounded ledger in addition to the prior Demo journey. It sends no
Paper Account mutation, snapshot, or reconciliation command.

## Isolation, upgrade, and packaging

Standard and Demo retain distinct Compose project names, named volumes,
databases, artifact roots, and modes. Deterministic regression coverage proves a
Demo installation does not change separate Standard storage. Standard startup
does not invoke the Demo installer and the 0007 migration seeds no account.

The installed-wheel migration-resource gate retains one exact packaged resource
tree and single head:

```text
0007_paper_account_ledger
```

It verifies:

- fresh installation to 0007;
- the supported historical populated 0005 forward path through 0006 to 0007;
- the populated 0006-to-0007 path while preserving the portfolio-review row and
  all earlier data;
- zero seeded Paper Accounts after migration; and
- fail-closed missing-resource and mismatched-head behavior.

No migration file, revision ID, ordering, schema authority, or startup repair
behavior changes in Sprint 187.

## Founder-owned acceptance

The consolidated operations runbook covers cold backup, existing-volume
upgrade, restart persistence, Demo v3 reset/install/replay, return to Standard,
and fail-closed recovery. The Founder owns:

- Docker image build/pull and Standard/Demo startup;
- complete stopped-workspace backup and external backup security;
- disposable Demo reset;
- preserved-volume and restart verification;
- bilingual browser acceptance;
- return-to-Standard isolation verification; and
- the merge decision.

Codex does not run Docker runtime acceptance, remove volumes, mutate a preserved
Founder volume, or claim browser acceptance.

## Preserved non-goals

Sprint 187 adds no market-data replay, trading calendar, session clock, strategy
runtime, order/fill lifecycle, execution simulator, PnL/equity calculation,
broker, QMT, MiniQMT, live, or real-money behavior. The synthetic opening
position is an explicit ledger adjustment, not an order, fill, or execution.
