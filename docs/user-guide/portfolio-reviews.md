# Portfolio Reviews

Portfolio Reviews let the Founder inspect one proposed component change against
an explicit static-weight portfolio scenario and record one human governance
decision.

This workspace presents historical review evidence. It does not forecast
performance, recommend a strategy, optimize weights, allocate capital, create a
Paper Account, place an order, or execute.

## Browse Reviews

Open **Portfolio Reviews** from the persistent navigation. The list is shown in
the exact order returned by the backend. Each row includes:

- review, source, and proposed-component IDs;
- localized status alongside its raw transport value;
- localized and raw created, updated, and reviewed timestamps;
- the complete analysis digest; and
- a link to the exact review detail.

Choose a status and limit, then select **Apply filters**. Merely changing a
control does not request new data. Use **Refresh** for a manual reread. The page
does not poll, rank, reorder, or remove duplicate records.

If refresh fails after a successful read, the prior evidence remains visible
with the new error. Keep the raw error code, operation, and request ID when
reporting the failure.

## Create a Review

Choose **Create portfolio review**. The complete manual builder remains
available. The integration region reads existing public research runs and
evidence manifests independently, in backend order, and never preselects them.

For an explicitly selected research run, choose a target component or add a new
component. Only exact strategy ID, optional experiment-name label, declared
symbol order, and one opaque `research_run` reference
`<experiment_slug>/<run_id>` may be copied. Component ID, returns, weights,
scenarios, audit fields, proposed component, and decision fields stay blank or
unchanged.

For an explicitly selected manifest, inspect raw manifest identity and grouped
references, select a target and compatible references, then add them. Type, ID,
label, and description are copied verbatim. Unsupported types remain visible
and cannot be mapped or imported; exact duplicates in one component are refused.
Governance, report, and lifecycle references are importable only when the exact
compatible reference already exists in a manifest.

Research metrics and browser comparison state are not aligned-return authority.
There is currently no persisted public `paper_comparison_summary` discovery
contract. Therefore aligned per-component return observations remain explicit
Founder input.

1. Enter a unique review ID and explicit `Idempotency-Key`.
2. Enter source audit fields, evaluation settings, and optional assumptions,
   warnings, or missing-evidence statements.
3. Define 2–12 components in authoritative order. Each component needs a
   strategy ID and at least one evidence reference. At least one component must
   contain a research-origin reference. Declared symbols are optional and are
   never inferred.
4. Enter at least three strictly increasing, timezone-aware observation
   timestamps and one finite return for every component at every timestamp.
5. Enter the baseline and proposed scenario identities, rationales, and exact
   non-negative static weights.
6. Select the proposed component explicitly.
7. Enter analysis audit fields and any analysis assumptions, warnings, or
   missing evidence.
8. Read and select the historical-evidence/non-execution confirmation, then
   choose **Create review**.

The form accepts strict decimal notation such as `0`, `0.25`, or `-0.1`.
Exponent notation such as `1e-3` is rejected. Entered values stay as text until
the complete form passes validation.

Each scenario displays the entered total. The page checks the backend weight
tolerance but never normalizes, rounds, recommends, or changes weights. It also
does not auto-select the proposed component.

Validation and API errors preserve every draft value. A created or exactly
replayed command remains on the same page and provides an explicit detail link.
Do not change an idempotency key to work around an uncertain response; first
determine whether the original command was accepted.

## Inspect Exact Evidence

The detail page reopens and displays backend-owned authority. Inspect:

- source identity, ordered components, evidence references, symbols, and every
  return observation;
- baseline and proposed scenarios and exact weight maps;
- concentration and component exposure;
- declared-symbol coverage and overlap;
- pairwise and candidate-to-baseline correlations;
- historical behavior, drawdown, and contribution;
- exact proposed-minus-baseline impacts;
- assumptions, warnings, and missing evidence;
- schema versions, digests, actors, and timestamps; and
- an immutable decision, if recorded.

Financial numbers are raw backend values. They are not percentage-formatted,
rounded, rescored, ranked, or colored as better or worse.

When overlap or correlation evidence says **Unavailable**, read the raw reason
and affected component IDs. Unavailable is not zero and must not be interpreted
as absence of risk or interaction.

Use **Refresh** to request newer authoritative detail. If refresh fails, the
previous successful evidence remains visible.

## Record the Human Decision

The decision form appears only while the raw status is
`awaiting_decision`. Enter:

- an explicit `Idempotency-Key`;
- decision ID;
- one explicit outcome: `approved`, `rejected`, or `deferred`;
- rationale and reviewer;
- a timezone-aware reviewed timestamp;
- ordered notes and warnings as needed; and
- the governance-only/non-execution confirmation.

No outcome is preselected. On success, the returned authoritative detail
replaces the page and the form disappears. A conflict or failure preserves all
evidence and decision inputs so you can inspect the error and refresh manually.
A settled review cannot receive a second decision.

Approval is governance evidence only. It does not mutate lifecycle state,
allocate cash, create holdings, authorize an order, or execute.

## Standard and Demo

Standard is unseeded and has no Demo loader. Demo dataset/descriptor v2 seeds
one exact isolated review, `demo-portfolio-review-001`, initially
`awaiting_decision`. Its visibly Demo-only create-example action requires
replace confirmation and only prefills the normal builder; it never auto-loads,
submits, or decides. Normal submission may return exact `replayed` authority.

A later valid `approved`, `rejected`, or `deferred` Demo decision persists across
exact Demo replay. It remains governance evidence only and has no M31 account or
execution effect. Existing Demo v1 storage conflicts with v2 and requires the
documented Founder-owned Demo-only reset; Standard storage must remain untouched.
