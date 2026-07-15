# Sprint 154 — Governance Evidence and Report Artifact Views

## Status

Complete.

## Objective

Deliver bounded, accessible Founder-facing inspection of the existing
governance-evidence and report-artifact APIs without changing backend, domain,
artifact, transport, or generated-contract authority.

## Delivered Routes

```text
/evidence-manifests
/evidence-manifests/[manifestType]/[artifactKey]
```

The list preserves backend deterministic order and shows the human-readable
manifest type, exact type and artifact key, manifest identity, backend-provided
reference count, creation metadata, label, and description. The detail route
encodes the exact type and key independently and renders the response according
to its generated OpenAPI discriminator.

## Evidence Configuration and States

The existing FastAPI evidence reader remains configured only through:

```text
EL_PSY_QUANT_EVIDENCE_ARTIFACT_ROOT
```

A reachable configured root with no supported manifests is a successful empty
state. An unset, missing, or unreadable root is the bounded
`evidence_artifact_root_unavailable` failure. An invalid supported artifact is
the bounded `evidence_artifact_invalid` failure. Exact missing selections use
`evidence_manifest_not_found`. Other API, transport, and malformed-response
failures retain a neutral bounded title, safe public message, request ID when
available, and manual retry where appropriate.

## Manifest Variants and Reference Authority

The detail view supports exactly:

- strategy decision manifests with summary and record reference groups
- report artifact manifests with label, description, notes, and references
- strategy review workflow manifests with state snapshot, transition proposal,
  and transition record reference groups

Each reference displays only its API-supplied schema version, type, ID, label,
and description. Group order, item order, and duplicate pointers are preserved.
References remain unresolved text and are not links or downloads. The Web layer
does not open referenced artifacts, access the filesystem, calculate totals,
deduplicate pointers, assess completeness, render reports, or infer lifecycle
state, approval, execution, recommendation, or governance meaning.

## Client, Navigation, and Accessibility

The endpoint-specific `fetchEvidenceManifests` and
`fetchEvidenceManifestDetail` clients derive success types from the checked-in
FastAPI OpenAPI contract. Lightweight runtime validation checks the discriminator
and all required common and variant fields before rendering. Stable public error
envelopes, request IDs, sanitization, stale-response suppression, the fixed
same-origin `/api/backend` transport, and the narrow Next.js rewrite are
unchanged.

Overview, Strategies/Research, and Governance/Reports are now the only enabled
workspace destinations. Loading uses one status region, failures use bounded
alerts, null values have a consistent `Not available` fallback, and long exact
identifiers wrap within responsive semantic content.

## Preserved Scope

Sprint 154 added no backend or OpenAPI change, report rendering, artifact
download, lifecycle mutation, approval action, paper-run control, financial
calculation, aggregation, ranking, scoring, chart, authentication, Docker,
broker, QMT, live, distributed, or S155–S159 behavior.

## Next Sprint

```text
Sprint 155 — Paper Run Launch and Status Workspace
```
