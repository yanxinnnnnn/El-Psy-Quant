# Founder Dashboard Information Architecture

## Purpose

This document defines the bounded information architecture for Sprint 164 —
Founder Dashboard and Workflow Information Architecture Refresh.

It does not add runtime components, aggregate APIs, ranking logic, or automatic
workflow decisions.

## Product Question

The future Overview should help the Founder answer five questions quickly:

```text
What workspace am I in?
Is the product healthy and configured?
What recent paper activity exists?
Which records may need explicit human attention?
What safe workflow action can I choose next?
```

The Dashboard is a decision-navigation surface, not a live market terminal or an
automatic recommendation engine.

## Core Principles

1. **Mode first.** Standard versus Demo identity is always visible.
2. **Health before activity.** The page distinguishes unreachable, unavailable,
   invalid, healthy-empty, and populated states.
3. **Existing evidence before synthesized insight.** The UI uses authoritative
   API data and does not invent scores or relationships.
4. **Attention is rule-bounded.** “Needs attention” means an explicit known
   workflow condition, not an AI opinion about strategy quality.
5. **Next actions are choices.** The product presents safe workflow options; it
   does not auto-run, auto-retry, auto-approve, or auto-transition.
6. **Raw detail remains inspectable.** Summary cards never replace exact record
   pages or audit data.
7. **Bilingual and accessible.** Information hierarchy must work in English and
   Simplified Chinese.

## Proposed Dashboard Regions

### 1. Workspace identity

Purpose:

- identify Standard or Demo mode;
- show Demo disposable-example warning;
- show active language;
- provide a bounded link to operating guidance where useful.

Existing contract:

- standard mode inferred from bounded Demo descriptor not-configured response;
- Demo mode identified through `GET /api/v1/demo-workspace`.

No new backend contract is required for basic mode identity.

### 2. Product readiness and configuration

Purpose:

- distinguish healthy product startup from unavailable data roots or database;
- tell the Founder whether there is no data or whether a dependency is invalid;
- provide bounded next-step guidance.

Existing contracts can partially support this through:

- `GET /api/v1/health` for process health;
- research list behavior;
- evidence-manifest list behavior;
- paper-job list behavior; and
- Demo descriptor behavior.

Limitations:

- `/health` is process health, not readiness;
- calling multiple business endpoints is currently required to infer workspace
  configuration;
- there is no single aggregate readiness contract.

S164 decision:

- a frontend-composed bounded readiness summary may use existing endpoints if it
  preserves individual errors and does not hide partial failure;
- any new aggregate readiness API must be separately specified and remain thin;
- S161 does not add such an API.

### 3. Recent paper activity

Purpose:

- show recent queued, running, succeeded, failed, or canceled jobs;
- make the exact job and result pages easy to reach;
- provide safe state-dependent actions only on existing detail pages unless an
  implementation issue explicitly approves Dashboard actions.

Existing contract:

- paper-job list endpoint supports product-owned records and status filtering;
- exact job and result endpoints provide authoritative detail.

Rules:

- preserve backend order;
- do not rank by profitability;
- operational `succeeded` means execution completed, not a favorable result;
- do not poll unless a later issue explicitly changes the manual-refresh rule;
- no hidden Run, Retry, Cancel, or Recover action from a summary card.

### 4. Available results and comparison continuation

Purpose:

- identify jobs with backend-owned `result_available`;
- offer an explicit route to exact result inspection;
- help the Founder start an ordered comparison using explicit selections.

Existing contract:

- succeeded-job/result availability list behavior;
- exact result endpoint;
- comparison route with repeated ordered `job_id` query parameters.

Rules:

- no automatic “best result” selection;
- no metric recomputation;
- no ranking, recommendation, or score;
- preserve explicit selection and order; and
- generic records are not assumed to belong to one research/governance chain.

### 5. Human-attention area

Purpose:

Surface bounded, explicit conditions that may require the Founder to inspect a
record or take a manual action.

Allowed attention conditions may include:

- failed Paper Job available for exact inspection;
- interrupted/running job eligible for existing manual recovery workflow;
- queued job awaiting an explicit Run decision;
- succeeded job with result available for review;
- an in-session lifecycle proposal awaiting an explicit human-review command;
- configured healthy workspace with no loaded evidence; or
- unavailable product dependency requiring operator action.

Important limitation:

The current lifecycle API is stateless and has no GET/list/current-state
endpoint. The Dashboard cannot claim durable pending lifecycle reviews unless a
later explicit backend contract is designed.

Rules:

- “attention” is operational/workflow state, not strategy quality;
- no recommendation to approve, reject, trade, or allocate capital;
- no automatic transition or job command;
- no inferred relationships between unrelated records;
- raw status/error identity remains available.

### 6. Guided workflow continuation

Purpose:

- preserve the Strategy-to-Human-Decision product narrative;
- offer user-chosen next actions;
- use exact Demo descriptor references in Demo mode;
- use generic browse actions in Standard mode unless exact links are supported by
  authoritative relationships.

Demo mode may provide:

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

Standard mode must not pretend that independent real records form one chain.

### 7. Recent evidence

Purpose:

- provide bounded access to saved research and governance/report manifests;
- show exact identity and type;
- help the Founder continue inspection.

Existing contracts:

- research-run list;
- evidence-manifest list.

Limitations:

- existing list semantics may not expose a universal “recent” ordering across
  root types;
- timestamps and ordering must not be fabricated;
- cross-type aggregation may require a later explicit product contract.

S164 may use separate recent/available sections preserving endpoint order rather
than inventing a merged chronology.

## Recommended Desktop Hierarchy

```text
Workspace shell
  -> workspace mode + language + product identity

Overview header
  -> product readiness summary
  -> bounded primary next action

Attention and activity
  -> attention conditions
  -> recent paper jobs

Evidence and results
  -> available results / comparison continuation
  -> research and governance evidence entry points

Workflow journey
  -> Demo exact guided chain OR Standard generic workflow map

Technical detail
  -> request IDs, errors, configuration guidance, refresh actions
```

The exact grid is a Sprint 164 visual implementation decision built on Sprint
163 design tokens.

## Recommended Mobile Hierarchy

```text
workspace identity
  -> health/configuration
  -> attention items
  -> recent paper activity
  -> result/review continuation
  -> evidence entry points
  -> workflow journey
  -> technical detail
```

Primary information must remain usable without horizontal page scrolling. Tables
may scroll within their own container.

## Existing API Coverage Matrix

| Dashboard need | Existing contract | S164 posture |
|---|---|---|
| Process health | `GET /api/v1/health` | Use as process health only. |
| Workspace mode | Demo descriptor enabled/disabled behavior | Use without hardcoded Demo IDs. |
| Research availability | research-run list | Preserve empty/unavailable/invalid distinctions. |
| Evidence availability | evidence-manifest list | Preserve type, order, and bounded errors. |
| Paper-job activity | paper-job list | Use backend status/order; no profitability meaning. |
| Exact paper result | job result endpoint | Link to authoritative inspection. |
| Comparison candidates | explicit user selection of available results | Never auto-rank or auto-select “best”. |
| Durable lifecycle attention | No existing GET/list contract | Do not claim persistent pending review. |
| Cross-workflow relationship | No general relationship contract | Do not infer links. |
| Aggregate readiness | No single approved contract | Compose carefully or specify a later thin API. |
| Unified recent timeline | No cross-source chronology contract | Keep sources separate unless a new contract is approved. |

## Potential Future API Needs

These are planning observations, not approved S161 implementation:

1. **Workspace readiness descriptor**
   - could expose bounded availability of configured product dependencies;
   - must not replace endpoint-specific authority;
   - must not expose filesystem paths.

2. **Dashboard activity summary**
   - could provide compact product-owned recent job/reference metadata;
   - must not duplicate full artifact payloads;
   - must preserve stable ordering semantics.

3. **Durable lifecycle review read model**
   - would require a separate governance and persistence decision;
   - cannot introduce a mutable independent `current_state` authority;
   - not automatically part of M29.

Any new API requires its own authoritative Issue and OpenAPI contract. S164 should
prefer existing APIs unless the missing contract blocks the agreed product
outcome.

## Action Rules

Dashboard actions are allowed only when their effect is explicit.

Allowed direction:

- inspect a record;
- browse a product area;
- open an existing exact job/result;
- start explicit comparison selection;
- open the existing submission or lifecycle review workspace;
- retry a failed read request; and
- navigate to documented operator guidance.

Not allowed:

- automatically Run a job;
- automatically Retry or Recover a job;
- automatically create or submit a lifecycle proposal;
- automatically approve/reject/defer;
- automatically select a strategy or result;
- recommend capital; or
- claim a strategy is ready for live trading.

## State Design

Every Dashboard region must support its own bounded state:

```text
loading
empty
available
partially available
unavailable
invalid
failed request
```

One failed region should not necessarily erase successful independent regions,
but partial availability must remain visible. The product must not present a
healthy aggregate when a required dependency failed.

## Localization Contract

- All product copy is available in `en` and `zh-CN`.
- Raw job status, lifecycle value, IDs, error codes, and UTC audit values remain
  available.
- Chinese copy must not turn operational attention into investment advice.
- Dashboard cards cannot rely on English string length.
- Accessibility labels follow the active locale.

## Success Criteria for Sprint 164

- Overview answers the five core product questions.
- Standard and Demo identity remain unmistakable.
- Existing API data is used without browser financial recomputation.
- Attention items are based only on explicit workflow conditions.
- No unsupported durable lifecycle state is implied.
- Generic Standard records are not falsely connected.
- Demo exact links remain descriptor-driven.
- English and Chinese layouts are complete and accessible.
- Primary and audit information are clearly separated.
- The complete M28 workflow remains reachable.
- Regression and production build gates pass.
