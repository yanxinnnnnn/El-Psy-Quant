# Milestone 26 — Paper Trading Application Service Foundation

## Status

Complete.

Milestone 26 was completed through Sprints 138–144.

## Objective

Add a thin local application-service and versioned API boundary over existing El-Psy-Quant domain capabilities without duplicating domain rules or changing artifact ownership.

## Architecture

```text
Browser
  -> future React/Next.js founder workspace
  -> FastAPI application API
  -> thin application services / use cases
  -> existing domain modules and artifact readers
```

Milestone 26 remains a modular monolith. Existing research, backtesting, paper, governance, report, and lifecycle modules remain authoritative. Existing local artifact files remain authoritative for completed outputs.

## Completed Sprint Sequence

| Sprint | Status | Deliverable |
|---:|---|---|
| S138 | Complete | Application service and API skeleton. |
| S139 | Complete | Strategy catalog and detail read services. |
| S140 | Complete | Research and backtest artifact inspection services. |
| S141 | Complete | Governance, report, and lifecycle evidence inspection services. |
| S142 | Complete | Paper run application command boundary. |
| S143 | Complete | Lifecycle proposal and human review application commands. |
| S144 | Complete | Milestone 26 closeout. |

## Sprint 138 Foundation

Sprint 138 provides:

- deterministic `create_app()` construction and `el_psy_quant.api.app:app`
- a reusable `/api/v1` version boundary
- `GET /api/v1/health` with an explicit Pydantic response
- a server-owned UUID `X-Request-ID` for request correlation
- stable Pydantic error envelopes for HTTP, validation, and unexpected errors
- sanitized unexpected failures that do not expose internal details

The health route proves only that the local application process can serve the API. It is not database, worker, broker, QMT, market-data, external-service, live-trading, or deployment readiness.

Local loopback command:

```text
uv run uvicorn el_psy_quant.api.app:app --host 127.0.0.1 --port 8000
```

## Guardrails

Milestone 26 does not add a product database, repositories, background workers, durable jobs, Web UI, authentication, broad CORS, arbitrary filesystem access, microservices, distributed infrastructure, broker or QMT integration, live execution, automatic lifecycle transitions, automatic strategy approval, or capital allocation.

API handlers remain thin. The application layer does not duplicate financial calculations, paper execution semantics, comparison logic, governance validation, lifecycle validation, or human-control rules.

## Sprint 139 Strategy Reads

Sprint 139 adds:

```text
GET /api/v1/strategies
GET /api/v1/strategies/{strategy_name}
```

The catalog is an immutable, deterministic in-memory description of built-in supported strategies only. Identity and order follow `supported_strategy_names()` exactly. The current catalog contains only `moving_average_crossover`. Its parameter metadata reflects the existing `MovingAverageCrossoverParameters` field order, required status, and defaults, but remains descriptive; existing configuration and domain validation are authoritative.

The catalog performs no strategy execution, experiment discovery, artifact inspection, market-data or network access, performance ranking, lifecycle-state inference, paper workflow action, persistence, background work, broker/QMT integration, live behavior, or capital allocation.

## Sprint 140 Research Artifact Reads

Sprint 140 configures one local root through `EL_PSY_QUANT_RESEARCH_ARTIFACT_ROOT` or an explicit `create_app(...)` override and adds:

```text
GET /api/v1/research-runs
GET /api/v1/research-runs/{experiment_slug}/{run_id}
```

Discovery is limited to direct experiment/run children. Symlinked directories and files are excluded, identifiers are exact, and all manifest-derived references are verified under the selected run. Listing reads fixed manifests only. Detail reads one fixed manifest and the single safely referenced metrics artifact. Saved metrics are validated and exposed without recomputation, aggregation, comparison, or ranking.

No HTTP input selects an artifact root or arbitrary file. Config, metadata, summary CSV, logs, raw outputs, governance, paper, lifecycle, persistence, jobs, UI, broker, QMT, live, and real-money behavior remain outside this sprint.

## Sprint 141 Evidence Manifest Reads

Sprint 141 configures an independent local root through `EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT` or an explicit `create_app(...)` override and adds:

```text
GET /api/v1/evidence-manifests
GET /api/v1/evidence-manifests/{manifest_type}/{artifact_key}
```

Discovery is limited to direct safe JSON files in the fixed `strategy-decisions`, `report-artifacts`, and `strategy-review` directories. Artifact keys select files and remain separate from domain manifest IDs. Saved top-level decision, report, and workflow manifests are reconstructed through their existing domain reference and manifest factories, which remain authoritative for validation.

References remain compact pointers and are never resolved. The service does not validate chain completeness, infer current lifecycle state or approval, render reports, execute commands, write artifacts, persist data, create jobs, add UI behavior, call brokers or QMT, imply live readiness, or allocate capital.

## Sprint 142 Paper Run Command

Sprint 142 adds exactly one synchronous command endpoint:

```text
POST /api/v1/paper-runs
```

The caller supplies explicit starting and ending paper account states, orders, and fills. The application command reconstructs existing domain objects through `create_paper_account_state(...)`, `create_paper_order_record(...)`, `create_paper_fill(...)`, and `create_paper_run_request(...)`, then executes only through `run_paper_trading_request(...)`. Domain normalization and session-summary behavior remain authoritative.

The response is the normalized in-memory artifact. The command does not generate orders, apply fills to derive or reconcile ending state, accept any path, execute configured-paper workflows, persist artifacts or result summaries, or create durable jobs, status, idempotency, retries, cancellation, recovery, repositories, or databases. `run_id` remains caller-supplied domain identity rather than a durable job ID. No broker, QMT, market-data stream, live execution, lifecycle transition, automatic approval, or capital allocation is implied.

## Sprint 143 Lifecycle Governance Commands

Sprint 143 adds exactly two synchronous command endpoints:

```text
POST /api/v1/lifecycle-transition-proposals
POST /api/v1/lifecycle-transition-records
```

Both commands are stateless and in memory. The application layer reconstructs source and resulting snapshots, evidence pointers, proposals, and review records only through the existing strategy-review domain factories. The review request carries the complete proposal because no repository, persisted resource, or ID lookup exists. Evidence references remain unresolved pointers and are never inspected.

An approved record requires a separate caller-supplied resulting snapshot matching the proposal strategy and target state. Approval is governance evidence only: it does not execute or apply a transition, mutate a snapshot, make any snapshot globally current, trigger paper or strategy behavior, or imply broker/live readiness. Rejected and deferred records prohibit a resulting snapshot.

No artifact, proposal, record, timeline, status, or current-state view is persisted. The commands add no registry, database, job, queue, worker, filesystem access, paper workflow, broker, QMT, live, real-money, or capital behavior.

## Sprint 144 Closeout

Sprint 144 verifies the completed application-service boundary and makes no runtime change.

The closeout confirms:

- all planned M26 read and command boundaries exist
- request IDs, explicit schemas, and stable sanitized errors remain consistent
- API routes remain thin and versioned
- existing domain factories remain authoritative
- configured artifact roots remain server-owned and bounded
- evidence pointers remain unresolved
- paper and lifecycle commands remain synchronous, in-memory, and non-persistent
- no database, durable job control, Web UI, broker, QMT, live execution, or capital behavior was introduced

See:

```text
docs/sprints/sprint-144-milestone-26-closeout.md
```

## Exit Criteria Verification

Milestone 26 is complete because:

- a deterministic local FastAPI application boundary exists
- explicit API request and response schemas exist
- stable sanitized errors and server-owned request IDs exist
- built-in strategies are inspectable through deterministic read models
- configured research artifacts and saved metrics are inspectable safely
- configured governance, report, and lifecycle manifests are inspectable safely
- existing explicit-input paper behavior is available through a thin synchronous command
- lifecycle proposals and human review records use existing strategy-review contracts
- existing domain and artifact ownership remains unchanged
- no product persistence, durable job control, background worker, Web UI, broker integration, or live behavior exists

## Preserved Boundaries

Milestone 26 did not introduce:

- SQLite, SQLAlchemy, migrations, repositories, or artifact indexes
- durable paper-job records, status, submission, retry, recovery, cancellation, or idempotency
- queues, workers, schedulers, or distributed infrastructure
- an independently authoritative lifecycle `current_state`
- automatic transitions, approvals, paper triggers, or capital decisions
- arbitrary filesystem access or evidence resolution
- Web UI, broad CORS, or authentication expansion
- broker or QMT integration
- market-data streaming, live execution, or real-money trading

Existing local artifact files remain authoritative. A future lifecycle current-state view must be derived from immutable snapshots and approved human records. Future mutable paper-job operational state must remain separate from lifecycle governance.

## Closeout Decision

Milestone 26 is complete.

The platform now has a stable local application/API boundary over selected existing capabilities. The next layer should add the smallest durable local persistence foundation needed for artifact indexing and manually controlled paper-job operation without weakening domain, artifact, lifecycle, or human-control boundaries.

## Next Milestone

```text
Milestone 27 — Persistence and Paper Job Control Foundation
```

## Next Sprint

```text
Sprint 145 — SQLite and SQLAlchemy Product Persistence Foundation
```
