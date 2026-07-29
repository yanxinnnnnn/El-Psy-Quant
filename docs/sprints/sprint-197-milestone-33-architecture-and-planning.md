# Sprint 197 — Milestone 33 Architecture and Planning

## Status

**Complete.**

GitHub Issue #389 is the authoritative M33 product, authority, domain,
idempotency, persistence, API, Web, Demo, recovery, migration, acceptance, and
sprint-sequence specification.

## Result

Sprint 197 froze:

- the M31 account/ledger and M32 market-time boundaries M33 must consume;
- the separation from research DataFrames, M15 `OrderIntent`, and legacy Paper
  order/fill evidence;
- Strategy Signal, account-bound Order Intent, and Pre-Trade Risk Decision as
  three distinct authorities;
- deterministic identity, digest, idempotency, concurrency, and recovery rules;
- the planned `0010_strategy_order_risk` migration boundary for S202;
- exactly nine planned versioned API operations;
- the generated-contract-only bilingual Founder Web boundary;
- isolated Demo v5 and restart/recovery evidence direction;
- M34 as the separate execution/fill/account-mutation authority; and
- the ordered S197–S206 implementation sequence.

Sprint 197 was documentation-only. It added no runtime code, tests, migrations,
schemas, Web behavior, Demo state, Docker behavior, or product state.

## Handoff

Sprint 198 begins the implementation sequence with pure runtime-reference,
market-reference, signal-command, Strategy Signal, and compact signal-reference
contracts only. All later evaluation, intent, risk, persistence, API, Web, Demo,
and execution work remains assigned to S199–S206.
