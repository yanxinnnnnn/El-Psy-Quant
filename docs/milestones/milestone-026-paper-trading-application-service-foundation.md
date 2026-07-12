# Milestone 26 — Paper Trading Application Service Foundation

## Status

In progress. Sprints 138 through 141 are complete.

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

## Sprint Sequence

| Sprint | Status | Deliverable |
|---:|---|---|
| S138 | Complete | Application service and API skeleton. |
| S139 | Complete | Strategy catalog and detail read services. |
| S140 | Complete | Research and backtest artifact inspection services. |
| S141 | Complete | Governance, report, and lifecycle evidence inspection services. |
| S142 | Planned | Paper run application command boundary. |
| S143 | Planned | Lifecycle proposal and human review application commands. |
| S144 | Planned | Milestone 26 closeout. |

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

API handlers must remain thin. The application layer must not duplicate financial calculations, paper execution semantics, comparison logic, governance validation, lifecycle validation, or human-control rules.

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

## Next Step

```text
Sprint 142 — Paper Run Application Command Boundary
```
