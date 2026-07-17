# Product Experience Direction — AI Quant Decision Workspace

## Purpose

This document defines the product-experience direction for Milestone 29. Sprint
163 now implements its visual-system constraints; Sprint 164 remains constrained
without adding Dashboard APIs or product behavior here.

## Product Position

El-Psy-Quant should feel like an **AI Quant Decision Workspace**:

- a focused local product for reviewing quantitative evidence;
- an explicit workspace for paper operations and human decisions;
- a calm, trustworthy environment for audit and recovery; and
- an AI-native product that assists navigation and understanding without taking
  control away from the Founder.

It should not feel like:

- an academic paper repository;
- an old enterprise administration console;
- a marketing landing page;
- a dense live-trading terminal;
- an autonomous strategy recommendation engine; or
- a broker dashboard.

## Experience Principles

### 1. Decision first

Every page should make the primary review question and safe next action obvious.
Supporting details remain available without competing with the main task.

### 2. Evidence before opinion

The product displays authoritative research, artifact, paper, comparison, and
governance evidence. It does not invent rankings, scores, recommendations, or
approval conclusions.

### 3. Calm operational confidence

The interface should communicate state clearly:

- what is loaded;
- what is missing;
- what is unavailable;
- what is queued or running;
- what failed;
- what can be safely retried; and
- what still requires explicit human review.

### 4. Progressive disclosure

Primary product meaning appears first. Raw IDs, schema versions, request IDs,
audit timestamps, and transport values remain available in a consistent detail
layer rather than dominating every card.

### 5. Bilingual by design

English and Simplified Chinese both shape component width, typography, spacing,
line length, table behavior, and mobile layout. The visual system is not approved
until both locales are usable.

### 6. Explicit human control

Buttons and guidance must distinguish:

- inspect from mutate;
- submit from run;
- retry from recover;
- propose from approve;
- review evidence from apply a lifecycle change; and
- Paper Trading from real-money trading.

## Product Identity

### Name

Retain the product name:

```text
El-Psy-Quant
```

Use a consistent descriptive context such as:

```text
Founder Quant Decision Workspace
创始人量化决策工作台
```

The product name is not translated.

### Tone

Product copy should be:

- direct;
- technically honest;
- calm;
- concise where action is required;
- explanatory where authority boundaries matter;
- free of hype and profit claims; and
- explicit about Demo data and human responsibility.

Avoid vague corporate filler and AI-marketing phrases.

## Visual Direction

### Color

Sprint 163 should define a modern neutral system with a restrained accent.

Desired properties:

- neutral page and surface hierarchy;
- high-contrast text;
- one clear primary action accent;
- semantic colors reserved for operational states;
- Demo identity that cannot be confused with standard mode;
- no decorative gradients that reduce readability; and
- no red/green-only meaning.

Sprint 163 locks the exact reviewable values in
`docs/product/visual-system.md` and verifies semantic token ownership
deterministically.

### Typography

Use a clean sans-serif direction with reliable English and Simplified Chinese
coverage.

Requirements:

- do not commit font binaries;
- do not depend on proprietary local fonts;
- use a safe system-font stack unless a separately reviewed web-font dependency
  provides clear product value;
- define monospace use for IDs, raw values, code, and audit details only;
- keep body line length readable;
- support Chinese punctuation and line breaking; and
- avoid typography whose Chinese fallback visibly changes weight or vertical
  rhythm.

### Spacing and density

The product should feel focused rather than sparse for decoration or dense for
technical completeness.

- group related fields into clear task sections;
- separate primary actions from destructive or recovery actions;
- provide enough vertical rhythm for long Chinese helper copy;
- keep repeated audit rows compact but readable;
- use responsive stacking instead of compressed unreadable columns; and
- avoid fixed heights for translated content.

## Information Hierarchy

Recommended page hierarchy:

```text
workspace identity and state
  -> page purpose
  -> primary review content
  -> primary safe action
  -> related workflow choices
  -> audit and technical details
```

A page should not begin with raw IDs unless the identity itself is the task.

### Primary level

- user question;
- state or result;
- major evidence summary;
- explicit next action.

### Secondary level

- supporting attributes;
- source and reference context;
- comparison detail;
- bounded warnings.

### Audit level

- raw domain/transport value;
- IDs and versions;
- request ID;
- exact UTC value;
- artifact reference; and
- retry/recovery diagnostic detail.

## Component Direction

### Workspace shell

The shell must provide:

- persistent product identity;
- persistent standard/Demo identity;
- primary navigation;
- language switcher;
- accessible skip navigation;
- responsive navigation behavior; and
- a stable location for future workspace health/attention indicators.

### Cards

Use cards only when they express a coherent object, decision, or state.

Cards should not become arbitrary containers around every paragraph.

A record card may contain:

- localized title;
- raw identity;
- status label plus raw status;
- key timestamps;
- one primary action; and
- secondary inspection actions.

### Tables

Tables remain appropriate for ordered records and exact comparison.

Requirements:

- preserve API order and duplicates;
- clear column hierarchy;
- sticky or repeated context only when it improves review;
- horizontal scrolling rather than destructive data omission;
- localized headers with raw field identity available where valuable;
- responsive alternatives for narrow screens when a table is no longer usable;
- no client-side ranking or recomputation; and
- semantic captions and headers.

### Forms

Forms should reflect user tasks rather than backend object nesting alone.

- explicit field groups;
- required/optional labels;
- examples and format guidance;
- technical mapping available without dominating the label;
- safe distinction between submission and execution;
- persistent validation summary plus field-level errors;
- no automatic submission after loading an example; and
- no language switch that silently discards entered values.

### Buttons and actions

Action hierarchy:

1. one clear primary action per task area;
2. secondary navigation or inspection;
3. bounded recovery action;
4. destructive/cancel action with appropriate confirmation.

Labels must describe the actual backend effect. Avoid generic “Confirm” where
“Run selected job” or “Record human review” is possible.

### Status indicators

A status indicator should include text, not color alone.

Where the status is an authoritative raw value, use:

```text
localized label
raw value
```

Operational success must not be styled or worded as strategy profitability.

### Empty states

A useful empty state explains:

- the product is reachable or not;
- what is empty;
- why this may be valid;
- what the Founder can choose next; and
- which action is operator-owned rather than browser-owned.

### Error states

A useful error state contains:

- localized title;
- localized bounded explanation;
- safe next step;
- raw stable error code;
- request ID when available;
- retry only where safe; and
- no internal path, stack trace, credential, or exception detail.

## Data Visualization Direction

M29 may improve visualization only when the backend exposes authoritative data
suitable for display.

Rules:

- do not synthesize time series in the browser;
- do not recompute metrics;
- do not create visual rankings presented as recommendations;
- label units and source clearly;
- preserve exact tabular/audit access;
- make uncertainty and missing data visible; and
- avoid decorative charts with no decision value.

Sprint 163 establishes reusable presentation foundations. Any new chart or
backend time-series contract requires an explicit implementation issue.

## Demo Workspace Identity

Demo mode must remain unmistakable after the refresh.

- persistent Demo label in the shell;
- clear disposable-example warning;
- semantic and accessible identity, not color alone;
- no wording that implies real evidence;
- no visual treatment identical to standard mode; and
- no hidden or dismissible-only warning.

The language switcher must localize the Demo explanation without changing the
backend descriptor identities.

## Responsive Direction

The Founder may use desktop as the primary operating surface, but all routes must
remain usable at narrow widths.

- navigation must remain reachable;
- primary actions must not disappear;
- forms stack predictably;
- tables scroll or adapt without changing record order;
- long Chinese text wraps without clipping;
- IDs can wrap or scroll without forcing the whole page wider;
- touch targets remain adequate; and
- modal/confirmation content remains readable.

## Accessibility Direction

At minimum:

- semantic landmarks and headings;
- keyboard-reachable navigation and controls;
- visible focus;
- correct label/control association;
- text alternatives for state and Demo identity;
- status/error announcements where appropriate;
- contrast validation;
- no color-only meaning;
- locale-correct accessible names; and
- motion kept minimal and non-essential.

## Dashboard Relationship

Sprint 163 creates the visual primitives. Sprint 164 applies them to the Overview
and navigation architecture.

The visual system must not bake in dashboard-specific data assumptions before
S164 confirms existing versus required API contracts.

## Acceptance Direction for Sprint 163

Sprint 163 should be considered successful when:

- one documented token system exists;
- the shell, typography, surfaces, forms, tables, actions, and states use it;
- both locales pass representative layout tests;
- Demo identity remains prominent;
- accessibility and contrast are verified;
- no domain or API semantics change;
- no new financial calculations appear; and
- the product feels coherent across the full M28 workflow.

## Risks and Guardrails

| Risk | Guardrail |
|---|---|
| “Modern” becomes decorative and less readable. | Decision hierarchy and accessibility outrank visual novelty. |
| Audit values disappear behind polished summaries. | Progressive disclosure preserves raw values and exact inspection. |
| Chinese fallback typography breaks layout. | Bilingual system-font review and representative content tests. |
| Status colors imply performance. | Text labels and semantics distinguish operational state from returns. |
| Dashboard density returns through reusable cards. | Cards require coherent object/state ownership and a primary question. |
| AI identity implies autonomous decisions. | Copy and actions preserve explicit Founder choice and human review. |
| Visual changes accidentally alter workflow behavior. | S163 does not change API/domain semantics and retains regression coverage. |

## Sprint 163 implementation record

Sprint 163 implements this direction across every existing route with:

- a neutral blue-accent light token system and no performance-signaling product
  palette;
- bilingual-safe system sans and exact-value monospace stacks;
- a solid responsive shell with persistent Paper/Demo identity and language
  switching;
- standardized action, status, state, card, panel, table, form, disclosure,
  audit, and workflow-step contracts;
- localized status meaning paired with exact raw values, including bounded
  neutral handling for unknown states;
- responsive rules for representative `360px`, `768px`, and `1280px+` widths;
  and
- visible focus, semantic HTML, text-plus-color state, and reduced-motion
  behavior.

The exact tokens, component inventory, state semantics, responsive and
accessibility rules, raw audit treatment, limitations, and Founder acceptance
checklist are authoritative in:

```text
docs/product/visual-system.md
```

This implementation does not change Overview information architecture, add
Dashboard aggregation, introduce charts, or alter backend/domain authority.
Founder local Standard/Demo visual acceptance remains pending before Sprint 164.
