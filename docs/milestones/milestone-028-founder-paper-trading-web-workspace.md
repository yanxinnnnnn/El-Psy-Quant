# Milestone 28 — Founder Paper Trading Web Workspace

## Status

**Complete.**

Milestone 28 completed after Sprint 160 was merged and the Founder locally verified the isolated Demo Workspace and the complete Strategy-to-Human-Decision journey.

## Objective

Deliver the first usable local Founder Web MVP over the existing application, persistence, artifact, paper-job, and governance foundations without weakening their authority boundaries.

The completed product remains:

- local-first;
- Founder-only;
- single-user with minimal authentication;
- Paper Trading only;
- review-oriented rather than latency-oriented; and
- a modular monolith.

## Delivered Sprint Chain

```text
S152 Next.js workspace shell and API client foundation
  -> S153 strategy and research views
  -> S154 governance evidence views
  -> S155 paper run launch and status workspace
  -> S156 portfolio result views
  -> S157 paper run comparison workspace
  -> S158 lifecycle proposal and human review workspace
  -> S159 minimal authentication, Docker Compose, and Engineering MVP closeout
  -> S160 isolated Founder Demo Workspace and first-run experience
```

## Delivered Founder Journey

```text
Strategy
  -> Research Evidence
  -> Governance Evidence
  -> Paper Run
  -> Portfolio Result
  -> Comparison
  -> Lifecycle Review
  -> Human Decision Evidence
```

The Founder can now:

- inspect registered strategy definitions;
- inspect saved research manifests and metrics;
- inspect governance and report manifests;
- submit and manually control durable paper jobs;
- inspect status, attempts, failures, recovery, and retry state;
- inspect authoritative succeeded paper results;
- compare two to four explicitly selected results without ranking or browser recomputation;
- create non-executing lifecycle proposals;
- record explicit human review evidence; and
- follow one coherent, isolated Demo Workspace journey on a fresh deployment.

## Productization Delivered

Milestone 28 added:

- a strict TypeScript Next.js App Router workspace;
- a fixed same-origin `/api/backend` gateway to the versioned FastAPI API;
- generated TypeScript contracts from the checked-in OpenAPI document;
- paired minimal Founder HTTP Basic authentication at the Web and API boundaries;
- reproducible standard Docker Compose startup;
- persistent local SQLite and artifact storage;
- an isolated, disposable Demo Compose project and volume;
- deterministic, validation-first Demo installation;
- explicit standard-workspace first-run empty-state guidance;
- product-facing user documentation; and
- authenticated end-to-end smoke verification.

## Authority Boundaries Preserved

### Domain authority

Existing research, backtesting, paper, comparison, governance, report, and lifecycle modules remain authoritative. The browser and API handlers do not become a competing financial or governance domain layer.

### Artifact authority

Completed artifact files remain payload authority. SQLite stores compact product metadata, indexes, paper-job operational state, attempts, idempotency data, and result references rather than complete artifact payloads.

### Browser boundary

The browser uses only the Web/API boundary. It never directly accesses SQLite, artifact roots, Python modules, Demo source files, QMT, MiniQMT, or a broker.

### Lifecycle authority

A lifecycle proposal remains non-executing. A human review record remains governance evidence. Neither silently mutates an independently authoritative current lifecycle state.

### Paper-job authority

Paper-job status remains mutable operational state and remains separate from strategy lifecycle governance.

### Demo isolation

Demo records are deterministic, visibly labeled, disposable, and isolated from standard user storage. Standard startup remains unseeded.

## Verification

Sprint 160 completed with:

- `uv run python scripts/check.py` passing;
- 2,125 Python tests passing and 3 skipped;
- 221 frontend tests passing;
- OpenAPI and generated-contract freshness checks passing;
- ESLint, strict TypeScript, and the production Next.js build passing;
- deterministic Demo installer success and replay verification;
- effective standard and Demo Compose configuration verification; and
- Founder local Docker verification of the complete guided Demo journey.

PR #315 merged with SHA:

```text
1c2a91431d90cc0da0b979cadded041e9d7329d6
```

## Explicit Non-goals

Milestone 28 did not add:

- automatic strategy ranking or recommendation;
- new financial calculations in the browser;
- automatic lifecycle transitions;
- mutable lifecycle current-state authority;
- capital allocation;
- broker, QMT, MiniQMT, or live trading behavior;
- distributed workers or queues;
- microservices, Kubernetes, Kafka, or Redis clusters;
- multi-user behavior, complex RBAC, or SaaS hosting; or
- a broad visual product refresh.

## Handoff to Milestone 29

Milestone 29 — Product Feedback and Hardening starts from real Founder usage.

The first priorities are:

1. formalize product-experience architecture and the feedback backlog;
2. add a complete English and Simplified Chinese product-language foundation;
3. build the modern visual system only after both languages can inform layout decisions;
4. refresh the Founder Dashboard and workflow information architecture; and
5. harden reliability, error surfaces, audit visibility, migrations, tests, and local deployment.

Planned sequence:

```text
S161 Founder Feedback and Product Experience Architecture
S162 Multilingual Foundation and Simplified Chinese Workspace
S163 Modern Visual System Foundation
S164 Founder Dashboard and Workflow Information Architecture Refresh
S165 Reliability, Idempotency, and Job Recovery Hardening
S166 Error Surface, Observability, and Audit Hardening
S167 Migration, Test, and Local Deployment Hardening
S168 Milestone 29 Closeout and M30 Handoff
```
