"use client";

import Link from "next/link";
import { useCallback } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { fetchEvidenceManifests } from "@/lib/api-client";
import {
  evidenceErrorTitle,
  evidenceManifestLabel,
  nullableText,
} from "@/lib/evidence-manifests";
import { useApiResource } from "@/lib/use-api-resource";

export function EvidenceManifestListView() {
  const request = useCallback(() => fetchEvidenceManifests(), []);
  const { state, retry } = useApiResource(request);

  return (
    <div className="business-workspace">
      <header className="page-heading">
        <p className="eyebrow">Governance and reports · Configured artifact root</p>
        <h1>Evidence manifests</h1>
        <p>
          Inspect backend-owned governance and report pointers in their deterministic API
          order. References remain unresolved, read-only evidence identifiers.
        </p>
      </header>

      {state.status === "loading" ? (
        <LoadingState message="Loading configured evidence manifests…" />
      ) : state.status === "error" ? (
        <ErrorState
          title={evidenceErrorTitle(state.code)}
          message={state.message}
          requestId={state.requestId}
          onRetry={retry}
        />
      ) : state.data.manifests.length === 0 ? (
        <EmptyState
          title="The configured evidence root is empty"
          message="The backend reached the configured root successfully and found no supported evidence manifests."
        />
      ) : (
        <ul className="card-list" aria-label="Evidence manifests">
          {state.data.manifests.map((manifest) => (
            <li
              className="record-card"
              key={`${manifest.manifest_type}/${manifest.artifact_key}`}
            >
              <div>
                <p className="record-card__meta">
                  {manifest.manifest_type} / {manifest.artifact_key}
                </p>
                <h2>{evidenceManifestLabel(manifest.manifest_type)}</h2>
                <dl className="compact-definitions compact-definitions--evidence">
                  <div><dt>Manifest ID</dt><dd>{manifest.manifest_id}</dd></div>
                  <div><dt>References</dt><dd>{manifest.reference_count}</dd></div>
                  <div><dt>Created by</dt><dd>{nullableText(manifest.created_by)}</dd></div>
                  <div><dt>Created</dt><dd>{nullableText(manifest.created_timestamp)}</dd></div>
                  <div><dt>Label</dt><dd>{nullableText(manifest.label)}</dd></div>
                  <div><dt>Description</dt><dd>{nullableText(manifest.description)}</dd></div>
                </dl>
              </div>
              <Link
                className="primary-link"
                href={`/evidence-manifests/${encodeURIComponent(manifest.manifest_type)}/${encodeURIComponent(manifest.artifact_key)}`}
              >
                Inspect manifest
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
