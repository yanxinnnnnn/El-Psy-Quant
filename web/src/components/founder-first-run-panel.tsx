"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { RequestId } from "@/components/data-states";
import {
  ApiClientError,
  fetchDemoWorkspace,
  fetchEvidenceManifests,
  fetchPaperJobs,
  fetchResearchRuns,
  type DemoWorkspaceDescriptorResponse,
} from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

type StandardWorkspaceState =
  | { status: "loading" }
  | { status: "empty" }
  | { status: "populated" }
  | { status: "error"; message: string; requestId: string | null };

function comparisonHref(jobIds: readonly string[]): string {
  const query = new URLSearchParams();
  jobIds.forEach((jobId) => query.append("job_id", jobId));
  return `/comparisons?${query.toString()}`;
}

function GuidedDemoJourney({ descriptor }: { descriptor: DemoWorkspaceDescriptorResponse }) {
  const research = descriptor.research_run;
  const paperStep = descriptor.evidence_manifests.length + 3;
  return (
    <section className="first-run-panel demo-journey" aria-labelledby="demo-journey-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Guided first run</p>
          <h2 id="demo-journey-title">Strategy to human decision evidence</h2>
        </div>
        <p>{descriptor.warning}</p>
      </div>
      <ol className="demo-journey__steps">
        <li><Link href={`/strategies/${encodeURIComponent(descriptor.canonical_strategy_name)}`}>1. Review the canonical strategy definition</Link></li>
        <li><Link href={`/research-runs/${encodeURIComponent(research.experiment_slug)}/${encodeURIComponent(research.run_id)}`}>2. Inspect saved research evidence</Link></li>
        {descriptor.evidence_manifests.map((reference, index) => (
          <li key={`${reference.manifest_type}/${reference.artifact_key}`}>
            <Link href={`/evidence-manifests/${encodeURIComponent(reference.manifest_type)}/${encodeURIComponent(reference.artifact_key)}`}>
              {index + 3}. Inspect {reference.manifest_type.replaceAll("_", " ")}
            </Link>
          </li>
        ))}
        <li><Link href={`/paper-jobs/${encodeURIComponent(descriptor.paper_jobs[0].job_id)}`}>{paperStep}. Inspect a succeeded paper job</Link></li>
        <li><Link href={`/portfolio-records/${encodeURIComponent(descriptor.paper_jobs[0].job_id)}`}>{paperStep + 1}. Inspect its authoritative portfolio result</Link></li>
        <li><Link href={comparisonHref(descriptor.comparison_candidate_job_ids)}>{paperStep + 2}. Compare the two ordered demo results</Link></li>
        <li><Link href="/lifecycle-review">{paperStep + 3}. Prepare a proposal and record explicit human decision evidence</Link></li>
      </ol>
      <p className="neutral-note">Each link comes from the validated backend descriptor. No fixture identity or evidence payload is defined in the browser.</p>
    </section>
  );
}

export function FounderFirstRunPanel() {
  const descriptorRequest = useCallback(() => fetchDemoWorkspace(), []);
  const { state: descriptorState, retry: retryDescriptor } = useApiResource(descriptorRequest);
  const [standardState, setStandardState] = useState<StandardWorkspaceState>({ status: "loading" });
  const sequence = useRef(0);
  const descriptorNotConfigured = descriptorState.status === "error" &&
    descriptorState.code === "demo_workspace_not_configured";

  const inspectStandard = useCallback(() => {
    const current = ++sequence.current;
    setStandardState({ status: "loading" });
    void Promise.all([
      fetchResearchRuns(),
      fetchEvidenceManifests(),
      fetchPaperJobs({ status: null, limit: 1 }),
    ]).then(([research, evidence, jobs]) => {
      if (current !== sequence.current) return;
      const empty = research.data.runs.length === 0 &&
        evidence.data.manifests.length === 0 && jobs.data.length === 0;
      setStandardState({ status: empty ? "empty" : "populated" });
    }).catch((error: unknown) => {
      if (current !== sequence.current) return;
      setStandardState({
        status: "error",
        message: error instanceof ApiClientError ? error.publicMessage : "Workspace evidence is unavailable.",
        requestId: error instanceof ApiClientError ? error.requestId : null,
      });
    });
  }, []);

  useEffect(() => {
    if (descriptorNotConfigured) {
      queueMicrotask(inspectStandard);
    }
    return () => { sequence.current += 1; };
  }, [descriptorNotConfigured, inspectStandard]);

  if (descriptorState.status === "loading") {
    return <section className="first-run-panel" role="status"><p>Discovering workspace mode…</p></section>;
  }
  if (descriptorState.status === "success") {
    return <GuidedDemoJourney descriptor={descriptorState.data} />;
  }
  if (descriptorState.code !== "demo_workspace_not_configured") {
    return (
      <section className="first-run-panel state-panel--error" role="alert">
        <h2>Workspace identity unavailable</h2>
        <p>{descriptorState.message}</p>
        <RequestId value={descriptorState.requestId} />
        <button className="retry-button" type="button" onClick={retryDescriptor}>Retry workspace discovery</button>
      </section>
    );
  }
  if (standardState.status === "loading") {
    return <section className="first-run-panel" role="status"><p>Checking the standard workspace for saved evidence…</p></section>;
  }
  if (standardState.status === "error") {
    return (
      <section className="first-run-panel state-panel--error" role="alert">
        <h2>Workspace data is unavailable, not empty</h2>
        <p>{standardState.message}</p><RequestId value={standardState.requestId} />
        <button className="retry-button" type="button" onClick={inspectStandard}>Retry evidence check</button>
      </section>
    );
  }
  if (standardState.status === "populated") {
    return <section className="first-run-panel"><h2>Standard workspace evidence is available</h2><p>Continue with the review workspaces below. These records are not automatically connected to one another.</p></section>;
  }
  return (
    <section className="first-run-panel" aria-labelledby="empty-workspace-title">
      <p className="eyebrow">Healthy standard workspace</p>
      <h2 id="empty-workspace-title">The application is running, but no workspace evidence has been loaded yet.</h2>
      <p>Empty is a valid first-run state. It is different from an unavailable, invalid, or failed research root, evidence root, or product database.</p>
      <p>Choose either the isolated Demo Workspace through the documented terminal commands, or load/create real artifacts through the documented operator workflows. This page never seeds data, writes artifacts, or initializes storage.</p>
    </section>
  );
}
