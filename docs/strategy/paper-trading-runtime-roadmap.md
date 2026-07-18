# Paper Trading Runtime Roadmap — M30 to M36

## Purpose

This document defines the Founder-approved route from the completed M29 product
to genuine market-driven and continuous Paper Trading.

It is an architectural sequence, not a fixed date or sprint commitment. Every
milestone requires its own planning Issue, architecture review, implementation
Issues, Founder acceptance, and manual merge.

## Starting Point After M29

El-Psy-Quant already provides:

- reproducible research and backtesting;
- explicit execution assumptions and Paper Trading records;
- file-authoritative Paper artifacts and result summaries;
- durable manually controlled Paper Jobs and attempts;
- comparison, promotion, decision, report, and lifecycle-review evidence;
- a bilingual Founder Web workspace;
- a modern decision-oriented Dashboard;
- stable errors, audit detail, request correlation, and sanitized local events;
- one exact SQLite/Alembic migration chain;
- fail-closed local Standard/Demo startup;
- isolated local storage and safe Demo reset; and
- complete Strategy-to-Human-Decision product acceptance.

The current Paper workflow is still request-driven. The Founder supplies the
starting/ending account state, orders, and fills that define the transaction
script. The platform validates, executes, persists, displays, compares, and
audits that script, but it does not yet create the trade from market data and
strategy output.

## Product Goal

```text
market data and trading time
  -> strategy decision
  -> portfolio/account-aware target exposure
  -> pre-trade risk
  -> Paper order lifecycle and simulated fills
  -> durable account and ledger update
  -> durable session checkpoint and recovery
  -> multi-day Paper operations
  -> explicit Founder review and control
```

## Approved Sequence

```text
M30 — Portfolio-Level Decision Review Foundation
M31 — Stateful Paper Account and Ledger Foundation
M32 — Market Data Replay, Trading Calendar, and Session Clock
M33 — Strategy-to-Order and Pre-Trade Risk Pipeline
M34 — Paper Execution Simulator and First True Paper Trading
M35 — Durable Paper Runtime and Recovery
M36 — Multi-day Paper Operations and Acceptance
```

## Cross-Milestone Architecture Rules

### Local-first modular monolith

M30–M36 may remain one local modular application with SQLite, authoritative
files, and explicit processes. Microservices or distributed infrastructure are
not default requirements.

### Durable truth before automation

```text
portfolio decision context
  -> account and ledger truth
  -> market-session truth
  -> order intent and risk truth
  -> execution truth
  -> runtime checkpoint truth
  -> multi-day operations
```

Later milestones must not invent state that an earlier milestone has not made
explicit and auditable.

### Human control

- Strategies are not automatically approved.
- Capital is not automatically allocated.
- Paper sessions and runtime controls remain explicit.
- Recovery never silently overwrites evidence.
- Operational automation does not become governance approval.

### Authority boundaries

- Domain modules own financial and risk calculations.
- Completed files remain artifact payload authority where applicable.
- SQLite owns compact durable account, ledger, order, session, and operational
  metadata only through explicitly approved schemas.
- Web and API presentation must not recompute or reinterpret financial truth.
- Broker-specific behavior remains outside the Paper domain.

### Determinism and auditability

Every transition must have stable identity, explicit inputs, deterministic
validation, bounded error behavior, and evidence sufficient to explain why the
account changed or did not change.

## M30 — Portfolio-Level Decision Review Foundation

### User-visible outcome

The Founder can evaluate a proposed strategy or Paper decision in portfolio
context rather than reviewing one strategy or one Paper result in isolation.

The workspace can answer:

```text
What portfolio is being reviewed?
What strategies and evidence are included?
What concentration and exposure already exist?
How may the proposed decision change portfolio risk or overlap?
What assumptions and limitations apply?
What explicit human decision was recorded?
```

### Core capability

- explicit portfolio-review identity;
- portfolio-level evidence references;
- concentration and exposure context;
- strategy interaction and overlap context;
- proposed portfolio impact;
- immutable review assumptions and warnings;
- explicit human decision record; and
- bilingual Web/API inspection and audit.

### Architecture boundary

M30 may introduce bounded portfolio review schemas, application services,
artifacts, and product records. It must reuse existing research, risk,
attribution, comparison, and governance authority rather than duplicate
calculations in the Web layer.

### Dependencies

- completed M14 portfolio risk and attribution foundations;
- completed M20–M24 governance foundations;
- completed M28–M29 Founder workspace and product hardening; and
- explicit Founder decision semantics.

### Exit criteria

- portfolio concentration, exposure, interaction, and proposed impact are
  reviewable through authoritative evidence;
- the decision record identifies inputs, assumptions, reviewer, timestamp,
  outcome, rationale, and warnings;
- raw portfolio/strategy/evidence identities remain visible;
- no decision automatically changes an account, creates an order, or allocates
  capital; and
- Founder acceptance confirms the workflow improves portfolio-level judgment.

### Non-goals

- automatic portfolio optimization;
- automatic capital allocation;
- strategy ranking or recommendation;
- account ledger mutation;
- Paper order generation;
- broker or live execution; and
- M31 implementation.

## M31 — Stateful Paper Account and Ledger Foundation

### User-visible outcome

The Founder can create and inspect a persistent virtual account whose cash,
positions, orders, fills, fees, and snapshots remain consistent across multiple
explicit Paper sessions.

### Core durable capability

At minimum:

```text
paper account
cash ledger
position ledger
order records
fill records
fees and adjustments
account version
session-linked snapshots
reconciliation result
```

The account must distinguish:

- starting cash from available and reserved cash;
- position quantity from average cost;
- realized from unrealized PnL where approved domain calculations exist;
- open, completed, canceled, and rejected order identity;
- immutable fills;
- ledger entries from derived account snapshots; and
- current durable version from historical evidence.

### Architecture boundary

- one account has one explicit durable identity;
- ledger entries are append-only or otherwise immutably auditable;
- account snapshots are derived/validated state, not competing hidden truth;
- writes use explicit optimistic or single-writer semantics;
- completed Paper artifacts may reference account/session identity but do not
  silently replace ledger truth; and
- migrations are explicit and reviewed.

### Dependencies

- M30 portfolio decision boundaries;
- existing Paper account/order/fill domain models;
- M27 persistence and Paper Job control;
- M29 migration and local-deployment hardening; and
- clear currency, precision, timestamp, and identity rules.

### Exit criteria

- a virtual account persists across process restarts;
- valid ledger events reproduce the same account state deterministically;
- duplicate fills or ledger entries cannot be applied silently;
- concurrent updates have one deterministic winner/loser contract;
- account, cash, position, order, fill, and snapshot audit is inspectable; and
- existing one-run Paper artifacts remain readable and authoritative for their
  historical payloads.

### Non-goals

- market data;
- strategy signal evaluation;
- automatic order generation;
- execution simulation over market time;
- scheduler or worker;
- broker account synchronization; and
- live trading.

## M32 — Market Data Replay, Trading Calendar, and Session Clock

### User-visible outcome

The Founder can select a validated historical market period and create explicit
Paper sessions that understand trading days, session boundaries, timestamps,
and market-data completeness.

### Core capability

- broker-neutral market-data interface;
- deterministic historical bar/quote replay;
- symbol and venue identity;
- trading calendar and holiday rules;
- timezone and session-open/session-close boundaries;
- explicit session ID and market timestamp progression;
- completeness and ordering validation;
- duplicate, missing, malformed, future, and stale-data rejection;
- adjusted/raw price policy where required;
- corporate-action boundary decision; and
- source/version/digest audit.

### Architecture boundary

- historical replay is the first supported source;
- data is validated before a Paper session can use it;
- the session clock advances only through explicit deterministic inputs;
- wall-clock time must not silently replace market time;
- network access is isolated behind an adapter and is not required for replay;
- source data and derived normalized data have explicit authority; and
- no browser directly reads local market-data files.

### Dependencies

- existing data-integrity and local-cache foundations;
- M31 account identity and session linkage;
- explicit supported asset/venue/calendar scope; and
- deterministic timestamp and timezone rules.

### Exit criteria

- the same validated replay input produces the same ordered market events;
- session open/close and trading-day identity are correct and auditable;
- missing, duplicate, out-of-order, stale, and invalid data fail visibly;
- Paper sessions cannot use data outside the approved session boundary; and
- Founder can inspect the data source, session, completeness, and limitations.

### Non-goals

- live streaming;
- exchange or broker feed integration;
- high-frequency event processing;
- WebSocket market terminal;
- automatic strategy execution;
- order generation; and
- distributed data infrastructure.

## M33 — Strategy-to-Order and Pre-Trade Risk Pipeline

### User-visible outcome

The Founder can select an approved strategy, account, symbols, and validated
market session. The platform evaluates the strategy and proposes risk-checked
Paper orders instead of requiring the Founder to write the orders manually.

### Core capability

```text
validated market state
  -> strategy signal
  -> target position / target weight / desired exposure
  -> current account comparison
  -> quantity and cash sizing
  -> order intent
  -> pre-trade risk decision
  -> accepted or rejected Paper order
```

Pre-trade controls should include an explicitly approved subset of:

- allowed account, strategy, symbol, and side;
- maximum order quantity and notional;
- maximum position and portfolio concentration;
- available/reserved cash;
- minimum lot or precision;
- maximum turnover;
- stale or missing price refusal;
- duplicate signal/order prevention;
- current open-order conflict;
- market-session guard;
- account-version guard; and
- explicit pause/kill control.

### Architecture boundary

- strategy output remains domain-owned and reproducible;
- target exposure is distinct from an executable order;
- sizing uses authoritative account and market state;
- order identity is deterministic and idempotent;
- risk decisions are explicit evidence with reason codes;
- rejected orders do not mutate the account; and
- no broker-specific field enters the core Paper order contract.

### Dependencies

- M30 portfolio-level decision context;
- M31 durable account and ledger;
- M32 validated market session and clock;
- stable strategy interface and configured workflow foundations; and
- approved risk limits and precision rules.

### Exit criteria

- identical strategy/account/market inputs produce the same order intent;
- current holdings and cash are included in sizing;
- duplicate generation cannot create a second accepted order silently;
- every accepted/rejected decision has stable identity and reason;
- the Founder can inspect signal, target, sizing, risk checks, and final order; and
- no manual order payload is required for the supported strategy path.

### Non-goals

- simulated fills;
- order-book or liquidity matching;
- background scheduling;
- continuous sessions;
- broker routing;
- automatic strategy approval; and
- automatic capital allocation outside approved limits.

## M34 — Paper Execution Simulator and First True Paper Trading

## Product Gate: First True Paper Trading

At M34 completion, the Founder can select:

```text
approved strategy
explicit Paper Account
supported symbols
validated historical market session
reviewed risk limits
execution-simulation assumptions
```

The platform itself performs:

```text
read validated market data
  -> evaluate strategy
  -> derive target exposure and Paper orders
  -> apply pre-trade risk
  -> advance order lifecycle through market time
  -> create simulated fills and fees
  -> update durable account and ledger
  -> persist session and audit evidence
```

The Founder no longer supplies orders and fills as the transaction script.

Manual session start is acceptable. Continuous automatic scheduling is not yet
required.

### User-visible outcome

The Founder can run one complete market-driven Paper session and inspect:

- strategy signal and target;
- generated order intent;
- risk decision;
- order lifecycle;
- partial/full fills or rejection;
- price, spread, slippage, latency, fee, and liquidity assumptions;
- account and position changes;
- session result and reconciliation; and
- complete raw audit identities.

### Core capability

An approved first version may support a bounded subset, but the architecture must
represent:

```text
queued / accepted / active / partially_filled / filled
canceled / rejected / expired
```

Execution behavior may include:

- market and limit orders;
- full and partial fill;
- deterministic spread and slippage;
- deterministic latency;
- fees, commissions, and tax assumptions;
- volume/liquidity limit;
- cancel and expiration;
- session-close handling;
- price-limit or halt refusal where supported; and
- duplicate-fill prevention.

### Architecture boundary

- the simulator consumes only validated orders and market events;
- fill identity is immutable and idempotent;
- account/ledger update and execution evidence use one atomic or explicitly
  recoverable boundary;
- simulation assumptions are versioned and visible;
- order success is not profitability;
- completed session artifacts remain reproducible; and
- no broker adapter is called.

### Dependencies

- M31 durable account and ledger;
- M32 market replay/session clock;
- M33 strategy-to-order and pre-trade risk;
- existing backtest execution-realism foundations; and
- approved order/fill state and precision contracts.

### Exit criteria

- at least one approved strategy completes a historical market-driven Paper
  session without Founder-authored orders or fills;
- account state before and after the session is durable and reconciled;
- order and fill identities are deterministic under replay;
- execution assumptions and every state transition are auditable;
- invalid/duplicate/uncertain outcomes fail without silent double application;
- bilingual Founder Web/API inspection is complete; and
- Founder accepts this as the first genuine Paper Trading workflow.

### Non-goals

- automatic recurring scheduling;
- multi-day continuous operation;
- multiple concurrent workers;
- real-time market streaming;
- broker routing;
- QMT/MiniQMT;
- real-money trading; and
- profitability claims.

## M35 — Durable Paper Runtime and Recovery

### User-visible outcome

A Paper session can be explicitly started, paused, resumed, inspected, and
recovered after interruption without duplicate account mutation or hidden
cleanup.

### Core capability

```text
durable session/work item
  -> claim
  -> checkpoint
  -> strategy/risk/order/execution/account steps
  -> terminal reconciliation
```

Expected contracts:

- durable session and work identity;
- explicit queued/running/paused/succeeded/failed/interrupted states;
- claim and ownership boundary;
- lease/heartbeat only if required by the chosen runtime;
- step checkpoint and resumability;
- deterministic event/application identity;
- bounded retry policy;
- missed or stale work detection;
- explicit pause, resume, cancel, and recover controls;
- safe shutdown; and
- reconciliation before terminal success.

### Architecture boundary

- a single local worker/process is sufficient unless evidence requires more;
- distributed systems are not a milestone goal;
- runtime state remains separate from strategy governance;
- recovery never invents a fill or overwrites an artifact;
- uncertain state remains visible and blocks unsafe continuation; and
- account mutation remains idempotent and version-guarded.

### Dependencies

- complete M34 single-session transaction chain;
- durable account and execution identities;
- M29 Paper Job reliability patterns; and
- explicit operational recovery policy.

### Exit criteria

- interruption at every approved checkpoint has deterministic recovery behavior;
- a resumed session cannot double-generate orders, fills, fees, or ledger entries;
- stale/uncertain sessions are visible and require an explicit safe decision;
- retry and recovery remain distinct;
- process restart preserves durable state and evidence; and
- Founder accepts the runtime control and recovery workflow.

### Non-goals

- multi-machine coordination;
- distributed queue infrastructure;
- high availability;
- live broker failover;
- automatic unattended recovery for uncertain financial state; and
- continuous multi-day acceptance.

## M36 — Multi-day Paper Operations and Acceptance

## Product Gate: Continuous Paper Trading

At M36 completion, one durable Paper Account can advance across multiple market
sessions and trading days with explicit operational controls and recovery.

### User-visible outcome

The Founder can:

- activate a reviewed Paper program;
- see the next/last session and market-data status;
- start or approve daily operation according to the chosen control model;
- inspect open orders, positions, cash, account version, and reconciliation;
- pause or stop new sessions;
- recover interrupted sessions;
- inspect daily and cumulative evidence; and
- review weeks of operation without rebuilding account state manually.

### Core capability

- multi-session account continuity;
- trading-day/session progression;
- session scheduling or explicit daily trigger;
- missed-session detection;
- open-order carry/expiry policy;
- daily mark and reconciliation;
- cumulative realized/unrealized and cost evidence where approved;
- bounded operational monitoring;
- durable pause/kill control;
- retention and audit navigation;
- backup/restore procedure for the runtime state; and
- extended acceptance under representative interruptions.

### Architecture boundary

- scheduling may remain local and simple;
- one explicit account writer is preferred;
- no unattended action proceeds after uncertain account/execution state;
- operational status is distinct from financial performance;
- account reconciliation is mandatory before session completion; and
- live execution remains outside the milestone.

### Dependencies

- M35 durable runtime and recovery;
- approved session/calendar policy;
- tested account reconciliation;
- bounded local operations and backup procedures; and
- Founder acceptance criteria for continuous use.

### Exit criteria

- the same account runs through a representative multi-day historical or delayed
  Paper period;
- no duplicate session, order, fill, fee, or ledger application occurs;
- interruption/restart/recovery scenarios preserve account truth;
- missed, stale, incomplete, and conflicting sessions remain visible;
- daily and cumulative reconciliation passes;
- operational controls and audit are complete in both locales; and
- Founder accepts the platform as a continuous multi-day Paper Trading product.

### Non-goals

- broker integration;
- QMT/MiniQMT;
- real-money execution;
- public uptime/SLA claims;
- multi-user operations;
- distributed high availability;
- automatic strategy approval; and
- automatic capital expansion.

## Delivery Gates

### Gate A — M30 governance readiness

Do not build automatic order generation before portfolio-level decision and
exposure context is explicit.

### Gate B — M31 account truth

Do not let market data or strategy automation mutate an account before the
ledger and reconciliation boundary is durable.

### Gate C — M32 market-time truth

Do not generate runtime orders from ambiguous, stale, incomplete, or unversioned
market data.

### Gate D — M33 risk ownership

Do not simulate execution for automatically generated orders that have no stable
risk decision and identity.

### Gate E — M34 first true Paper Trading

Do not claim genuine Paper Trading while the Founder still supplies both the
orders and fills.

### Gate F — M35 durability

Do not claim reliable operation when process interruption can double-apply or
silently lose transaction state.

### Gate G — M36 continuous operations

Do not claim continuous Paper Trading until one account survives and reconciles
across multiple trading days and representative failures.

## Beyond M36

M36 is not live-trading approval.

A later explicit roadmap must separately establish:

- execution-risk governance;
- live-readiness controls;
- broker-neutral execution commands;
- adapter isolation;
- broker/QMT capability assessment;
- capital and exposure limits;
- kill and incident controls;
- production operational readiness; and
- explicit Founder authorization.

No browser-to-broker or browser-to-QMT direct connection is permitted.
