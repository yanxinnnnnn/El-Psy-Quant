# Founder Web Visual System

## Status and ownership

Sprint 163 implements this visual system across the complete Founder Web
workspace. The Web application owns the runtime tokens and class contracts in
`web/src/app/globals.css`; `web/src/components/ui/status-badge.tsx` owns the
shared operational-status primitive. Founder local rendered acceptance remains
pending.

The system is light-only, local-first, bilingual, decision-oriented, and
audit-friendly. It does not add product behavior, Dashboard aggregation,
financial calculation, recommendation, ranking, charting, or execution
authority.

## Principles

1. Product meaning and the safe next human action precede decoration.
2. Raw domain, transport, artifact, user-entered, ordered, duplicate, and
   quantitative truth remains visible.
3. Operational state uses text plus restrained color; it never represents
   profitability or investment quality.
4. English and Simplified Chinese share one layout system without shortened
   translations or fixed text heights.
5. Demo identity is persistent text and warning content, not a color-only cue.
6. Keyboard, focus, contrast, semantic HTML, and reduced-motion behavior are
   baseline contracts.

## Semantic tokens

### Color

| Token | Exact value | Use |
|---|---|---|
| `--color-canvas` | `#f3f5f8` | Application canvas |
| `--color-surface-primary` | `#ffffff` | Primary content surface |
| `--color-surface-elevated` | `#ffffff` | Raised surface |
| `--color-surface-muted` | `#f7f8fa` | Supporting surface |
| `--color-surface-inset` | `#edf1f5` | Inset/grouped surface |
| `--color-text-primary` | `#172033` | Primary text |
| `--color-text-secondary` | `#526174` | Supporting text |
| `--color-text-tertiary` | `#68778a` | Captions and raw secondary detail |
| `--color-border-subtle` | `#dce2e9` | Default boundary |
| `--color-border-strong` | `#aeb9c6` | Data/control boundary |
| `--color-accent` | `#3756b2` | Primary action and active navigation |
| `--color-accent-hover` | `#2d478f` | Primary hover |
| `--color-accent-soft` | `#e8edff` | Selected/supporting accent surface |
| `--color-link` | `#294d9b` | Text link |
| `--color-link-hover` | `#203d7b` | Text-link hover |
| `--color-focus` | `#1769d2` | Visible focus outline |
| `--color-state-neutral` | `#4f6074` | Neutral/unknown state |
| `--color-state-neutral-soft` | `#edf1f5` | Neutral-state surface |
| `--color-state-info` | `#2859a6` | Informational/active state |
| `--color-state-info-soft` | `#e8f0ff` | Informational surface |
| `--color-state-success` | `#176b72` | Operational completion only |
| `--color-state-success-soft` | `#e0f3f2` | Operational completion surface |
| `--color-state-warning` | `#8a5700` | Pending, recovery, or caution |
| `--color-state-warning-soft` | `#fff1cf` | Warning surface |
| `--color-state-danger` | `#a1353f` | Failure, validation, destructive action |
| `--color-state-danger-soft` | `#fdebed` | Danger/error surface |
| `--color-state-unavailable` | `#6b5967` | Unavailable/canceled state |
| `--color-state-unavailable-soft` | `#f2edf1` | Unavailable-state surface |
| `--color-state-disabled` | `#6f7b89` | Disabled control text |
| `--color-state-disabled-soft` | `#e8ebef` | Disabled control surface |
| `--color-demo` | `#704a00` | Demo text |
| `--color-demo-surface` | `#fff4d8` | Demo warning surface |
| `--color-demo-border` | `#b67812` | Demo boundary |

Compatibility aliases in `globals.css` point only to these semantic owners;
they do not own duplicate literal values.

### Typography

The system sans stack is:

```css
-apple-system, BlinkMacSystemFont, "Segoe UI Variable", "Segoe UI",
"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC",
"Noto Sans SC", system-ui, sans-serif
```

The exact-value stack is:

```css
"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace
```

The scale is caption `0.75rem`, label `0.8125rem`, body `0.9375rem`, large body
`1.0625rem`, responsive section `1.25rem–1.625rem`, and responsive page title
`2rem–3.25rem`. Body line height is `1.62`; title line height is `1.18`. Raw
values and quantitative tables use tabular numerals. No external font request or
committed font file is permitted.

### Spacing, shape, elevation, controls, and motion

- spacing: `0.25`, `0.5`, `0.75`, `1`, `1.25`, `1.5`, `2`, `2.5`, and `3rem`;
- radii: `0.375rem`, `0.625rem`, `0.875rem`, and pill `999px`;
- borders: one-pixel subtle and strong semantic borders;
- elevation: `0 1px 2px rgb(23 32 51 / 5%)` at rest and
  `0 8px 24px rgb(23 32 51 / 7%)` when raised;
- controls: `2.25rem`, `2.75rem`, and `3rem` minimum heights, never fixed text
  heights;
- shell: `4.75rem` desktop header and `16.5rem` desktop sidebar;
- content: `78rem` application maximum and `52rem` reading maximum; and
- motion: `120ms` fast and `180ms` standard with
  `cubic-bezier(0.2, 0, 0, 1)` only for clarity.

The documented representative widths are `360px`, `768px`, and `1280px`.
Layout rules also use intermediate `480px`, `767px`, and `1024px` CSS thresholds
to protect content before those representative widths become constrained.

## Shell and navigation

The shell retains the product name, Founder decision-workspace context,
authenticated local-product framing, route-aware navigation, milestone note,
language switcher, skip link, Paper environment identity, and Demo identity.

- Desktop uses a solid header and bounded sidebar.
- Tablet uses horizontally scrollable, keyboard-accessible primary navigation.
- Narrow screens stack the header tools; environment identity and the language
  switcher remain visible.
- Demo always shows the localized `Demo Workspace` label and disposable-data
  warning with a dedicated border and text, on every route.
- Active navigation uses `aria-current="page"` and explicit current-state text.

The shell does not change routes, locale-cookie behavior, ordered query
parameters, or in-progress Paper Job/Lifecycle state.

## Primitive and class-contract inventory

- page: `.page-heading`, `.eyebrow`, `.identity-line`;
- sections: `.content-panel`, `.related-panel`, `.subsection`,
  `.section-heading`;
- actions: `.primary-button`, `.secondary-button`, `.quiet-button`,
  `.warning-button`, `.danger-button`, `.primary-link`, `.text-link`;
- objects: `.record-card`, `.card-list`, `.definition-grid`,
  `.compact-definitions`, `.artifact-list`;
- state: `StatusBadge`, `.state-panel--loading`, `.state-panel--empty`,
  `.state-panel--error`, notices, mutation records, and confirmation regions;
- data: `.table-scroll`, semantic captions/headers, `.localized-value`,
  `.raw-value`, and `.audit-disclosure`;
- forms: `.form-section`, `.form-grid`, `.repeatable-row`, required/optional
  labels, field guidance, field errors, and action bars; and
- journey: ordered Demo steps and lifecycle timelines.

These are bounded contracts for patterns already present, not a speculative UI
framework.

## Operational state semantics

| State | Treatment | Meaning boundary |
|---|---|---|
| queued, running | informational | Work is pending/active, not complete |
| succeeded, available | operational completion | Not profitable or recommended |
| failed | danger | Operational failure, not investment loss |
| canceled, unavailable | unavailable | No completion claim |
| interrupted, warning, recover | warning | Explicit human attention/action |
| invalid | danger with detail | Distinct from empty |
| empty | neutral state panel | May be a healthy first-run state |
| deferred, on hold | warning | No approval or execution |
| rejected | danger plus text | Explicit governance outcome only |
| approved | informational plus raw value | Human evidence, not runtime execution |
| unknown | neutral plus exact raw value | No invented interpretation |
| Demo | dedicated Demo label/warning | Disposable example evidence |
| Standard/Paper | neutral environment label | Local Paper Trading only |

Every authoritative status badge includes localized text and its raw value.

## Tables, raw values, and audit detail

Tables preserve columns, API order, duplicates, raw cells, and captions. Their
containers own horizontal scrolling so the page does not. Quantitative values
are never recomputed. Long IDs, keys, paths, versions, timestamps, and code wrap
at safe boundaries outside tables and remain contained inside table scrolling.
Localized number/time presentation keeps a visible exact raw representation.
Sanitized backend detail uses keyboard-accessible `details`/`summary`; it is
visually secondary but never removed or hover-only.

## Bilingual and responsive rules

- All text-bearing controls use minimum height and allow wrapping.
- English and Simplified Chinese use the same system stack and spacing tokens.
- Form grids collapse from three columns to two and then one.
- Repeatable Paper Job and Lifecycle rows collapse without reordering values.
- Tables and navigation scroll within their own bounded containers.
- At `360px`, environment/Demo identity, language choice, actions, form fields,
  warnings, IDs, and navigation remain reachable without global overflow.

## Accessibility

The system preserves landmarks, heading order, named navigation, captions,
fieldsets, legends, labels, alerts, status regions, and disclosures. Focus uses
a visible three-pixel outline/halo. Hover is supplemental. State is not
color-only. Disabled controls remain legible and explicit. Motion is minimal;
`prefers-reduced-motion: reduce` removes smooth scrolling and reduces animation
and transition duration to `0.01ms`.

## Known limitations

- Deterministic tests validate tokens, semantic markup, responsive contracts,
  and meaning; they do not replace real browser rendering.
- No dark mode, external fonts, charting, icon framework, broad UI library, or
  screenshot service is included.
- Sprint 163 does not restructure Overview or add S164 Dashboard information.
- Founder Standard/Demo visual acceptance remains required before merge and
  before Sprint 164 begins.

## Founder local acceptance checklist

In Standard and Demo, check English and Simplified Chinese at approximately
`360px`, `768px`, and `1280px+`:

- visit every existing list, detail, form, comparison, and lifecycle route;
- inspect loading, empty, invalid, unavailable, error, success, conflict, and
  partial-failure states available locally;
- confirm the environment identity, Demo warning, navigation, skip link, and
  language switcher remain visible and keyboard-operable;
- switch locale with ordered comparison parameters and unsaved Paper
  Job/Lifecycle fields present;
- inspect long IDs, raw UTC values, schema versions, code, tables, disclosures,
  repeated records, and duplicates;
- operate Paper Job confirmations and Lifecycle proposal/review boundaries
  without changing their semantics; and
- confirm there is no page-level horizontal overflow; bounded table/navigation
  scrolling is expected.
