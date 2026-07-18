# Milestone 29 — Product Feedback and Hardening

## Status

**Complete.**

Milestone 29 completed after Sprints 161–167 were merged, the Founder completed
Standard/Demo acceptance, and Sprint 168 formalized the closeout and M30–M36
handoff.

## Objective

Turn the completed M28 local Founder Web MVP into a bilingual, modern,
actionable, and dependable product suitable for routine Founder use without
adding speculative quantitative or trading-runtime behavior.

## Delivered Sprint Chain

```text
S161 Founder Feedback and Product Experience Architecture
  -> S162 Multilingual Foundation and Simplified Chinese Workspace
  -> S163 Modern Visual System Foundation
  -> S164 Founder Dashboard and Workflow Information Architecture Refresh
  -> S165 Reliability, Idempotency, and Job Recovery Hardening
  -> S166 Error Surface, Observability, and Audit Hardening
  -> S167 Migration, Test, and Local Deployment Hardening
  -> S168 Milestone 29 Closeout and M30–M36 Handoff
```

## Delivered Product Outcome

```text
usable local Founder MVP
  -> complete English / Simplified Chinese product
  -> modern responsive decision workspace
  -> bounded daily-use Dashboard
  -> understandable Paper Job control and recovery
  -> actionable errors and audit evidence
  -> safe local migration and deployment
  -> explicit future route to genuine Paper Trading
```

### Complete bilingual product

- Supported locales remain exactly `en` and `zh-CN`.
- English remains the default and fallback.
- Existing routes remain unprefixed.
- A validated local cookie stores the display preference.
- The language switcher preserves current route, ordered query parameters, and
  in-progress form state.
- Catalog validation enforces exact locale, namespace, and key parity.
- Raw IDs, states, error codes, timestamps, quantitative values, user text,
  artifact text, order, and duplicates remain authoritative and untranslated.

### Modern visual system

- One semantic token system owns color, typography, spacing, borders, radius,
  elevation, control sizing, focus, motion, shell dimensions, and responsive
  thresholds.
- The product uses bilingual-safe system typography.
- Shared shell, navigation, actions, status, cards, panels, tables, forms,
  disclosures, confirmations, states, and audit-detail patterns cover every
  current route.
- Standard/Paper and Demo identity remain persistent and unmistakable.
- Narrow, tablet, and desktop behavior preserves information rather than hiding
  raw data.

### Founder Dashboard

Overview now answers bounded operational questions:

```text
What workspace am I in?
Is the process and required local data available?
What recent Paper Job activity exists?
Which records may need explicit human attention?
What safe navigation or inspection action can I choose next?
```

The Dashboard:

- composes existing health, Demo descriptor, research, evidence, and Paper Job
  reads;
- keeps independent success, loading, empty, and failure states;
- preserves partial availability;
- shows source-specific recovery and request identity;
- preserves backend order, duplicates, raw status, timestamps, and exact links;
- supports explicit ordered comparison selection; and
- performs no ranking, recommendation, capital allocation, command, or browser
  financial recomputation.

### Paper Job reliability and recovery

M29 hardened the existing durable job model without changing its state machine:

```text
queued
running
succeeded
failed
canceled
```

Delivered behavior includes:

- explicit `created` versus exact `replayed` submission outcome;
- deterministic idempotency conflict;
- atomic Run claim and numbered attempt before HTTP acceptance;
- one non-durable post-response execution callback over the existing claim;
- state-dependent available actions;
- clean-output, non-executing Retry;
- explicit UTC-threshold Recover with `requeued`, `succeeded`, or `failed`
  outcomes;
- exclusive file creation and result/reference collision protection;
- concurrency winner/loser behavior;
- settled evidence retained during pending, refresh, and command failure; and
- no hidden polling, retry, recovery, cleanup, overwrite, or follow-on command.

### Error, observability, and audit hardening

- One static backend error inventory covers every stable reachable code.
- One matching Web inventory supplies semantic category, localized title,
  explanation, recovery, and safe unknown fallback.
- Shared error surfaces distinguish authentication, not found, invalid,
  conflict, unavailable, protocol, internal, and unknown conditions.
- Technical audit detail preserves operation, HTTP status, entity, raw code,
  request ID, and bounded backend public message.
- Python standard-library logging emits bounded sanitized request-completion,
  successful Paper Job command, and terminal claimed-execution events.
- Static operation and route-template catalogs prevent concrete path/query
  leakage.
- Credentials, headers, cookies, bodies, idempotency keys, filesystem paths, SQL,
  exception text, tracebacks, and financial/artifact payloads remain excluded.
- All approved attempt error codes have bilingual meaning and safe recovery
  guidance.

### Migration and local deployment hardening

The exact migration chain remains:

```text
0001_product_baseline
  -> 0002_artifact_index
  -> 0003_paper_jobs
  -> 0004_paper_job_recovery_audit
  -> 0005_paper_job_result_references
```

M29 delivered:

- one application-owned current revision checked against Alembic's single head;
- upgrade and data-preservation coverage from every historical revision;
- repeat-at-head no-op behavior;
- read-only schema and workspace verification;
- refusal of unversioned, malformed, multi-row, unknown, or newer existing
  Standard databases before Alembic can change them;
- startup ordering of migrate/install, verify, then serve;
- exact Standard/Demo project and volume isolation;
- locked Python build and runtime exports derived from `uv.lock`;
- runtime-only final backend image and `npm ci` Web installation;
- bilingual non-mutating same-origin smoke verification;
- cold-backup and existing-volume upgrade guidance;
- Demo-only reset and verified return to Standard; and
- explicit restore limitations without an automatic destructive helper.

## Authority Boundaries Preserved

### Domain authority

Research, backtesting, Paper Trading, comparison, governance, report, and
lifecycle modules remain authoritative. Web and API presentation do not become a
competing financial or governance domain.

### Artifact authority

Completed files remain payload authority. SQLite stores compact indexes,
references, job state, attempts, idempotency records, and result references.

### Browser boundary

The browser uses only the same-origin Web/API boundary. It never directly
accesses SQLite, artifact roots, Python modules, Demo source files, QMT,
MiniQMT, or a broker.

### Lifecycle authority

Lifecycle proposals remain non-executing. Human review remains explicit
immutable evidence and does not silently mutate an independently authoritative
current state.

### Paper Job authority

Paper Job state remains mutable operational state separate from lifecycle
governance. Idempotency remains replay-safe submission identity, not an
exactly-once execution claim.

### Demo isolation

Demo records remain deterministic, visibly labeled, disposable, and isolated
from Standard storage. Standard startup remains unseeded.

## Verification and Founder Acceptance

M29 completion is supported by:

- repository quality-gate success for each implementation sprint;
- exact bilingual catalog and route coverage;
- responsive/accessibility verification;
- concurrency, rollback, error, redaction, migration, startup, and isolation
  regression coverage;
- static Standard/Demo Compose verification;
- Founder Standard/Demo acceptance in both locales;
- Founder reliability, error/observability, migration/deployment, persistence,
  Demo reset, and return-to-Standard acceptance; and
- manual Founder merge of every implementation PR.

## Explicit Non-goals

M29 did not add:

- strategy profitability or alpha evidence;
- external-user or market validation;
- a persistent Paper Account ledger across sessions;
- market-data/session-clock runtime;
- automatic strategy-to-order conversion;
- pre-trade risk for automatic orders;
- a runtime order lifecycle or execution simulator;
- a durable multi-session worker/checkpoint loop;
- continuous multi-day Paper Trading;
- broker, QMT, MiniQMT, or live execution;
- automatic strategy ranking, approval, or capital allocation;
- public SaaS, complex RBAC, or multi-tenancy; or
- distributed infrastructure.

## Handoff

Milestone 30 begins portfolio-level human decision review. Milestones 31–36 then
build the stateful account, market-session, strategy-to-order, execution,
runtime, and operations layers required for genuine Paper Trading.

```text
M30 Portfolio-Level Decision Review Foundation
M31 Stateful Paper Account and Ledger Foundation
M32 Market Data Replay, Trading Calendar, and Session Clock
M33 Strategy-to-Order and Pre-Trade Risk Pipeline
M34 Paper Execution Simulator and First True Paper Trading
M35 Durable Paper Runtime and Recovery
M36 Multi-day Paper Operations and Acceptance
```

M34 is the first genuine market/strategy-driven Paper Trading gate. M36 is the
continuous multi-day Paper Trading gate.

See:

```text
docs/strategy/paper-trading-runtime-roadmap.md
```
