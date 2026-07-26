"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { ErrorState } from "@/components/data-states";
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
  | {
      status: "error";
      code: string | null;
      message: string | null;
      requestId: string | null;
      httpStatus: number | null;
      operation: string;
    };

type ManifestTypeLabelKey =
  | "reportArtifact"
  | "strategyDecision"
  | "strategyReviewWorkflow"
  | "unknown";

function manifestTypeLabelKey(manifestType: string): ManifestTypeLabelKey {
  switch (manifestType) {
    case "report_artifact_manifest":
      return "reportArtifact";
    case "strategy_decision_manifest":
      return "strategyDecision";
    case "strategy_review_workflow_manifest":
      return "strategyReviewWorkflow";
    default:
      return "unknown";
  }
}

function comparisonHref(jobIds: readonly string[]): string {
  const query = new URLSearchParams();
  jobIds.forEach((jobId) => query.append("job_id", jobId));
  return `/comparisons?${query.toString()}`;
}

function GuidedDemoJourney({ descriptor }: { descriptor: DemoWorkspaceDescriptorResponse }) {
  const t = useTranslations("overview.firstRun");
  const research = descriptor.research_run;
  const paperStep = descriptor.evidence_manifests.length + 3;
  return (
    <section className="first-run-panel demo-journey" aria-labelledby="demo-journey-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("demoEyebrow")}</p>
          <h2 id="demo-journey-title">{t("demoTitle")}</h2>
        </div>
        <p>{t("demoWarning")}</p>
      </div>
      <ol className="demo-journey__steps">
        <li><Link href={`/strategies/${encodeURIComponent(descriptor.canonical_strategy_name)}`}>{t("strategyStep", { step: 1 })}</Link></li>
        <li><Link href={`/research-runs/${encodeURIComponent(research.experiment_slug)}/${encodeURIComponent(research.run_id)}`}>{t("researchStep", { step: 2 })}</Link></li>
        {descriptor.evidence_manifests.map((reference, index) => {
          const labelKey = manifestTypeLabelKey(reference.manifest_type);
          return (
            <li key={`${reference.manifest_type}/${reference.artifact_key}`}>
              <Link href={`/evidence-manifests/${encodeURIComponent(reference.manifest_type)}/${encodeURIComponent(reference.artifact_key)}`}>
                <span>{t("manifestStep", { step: index + 3, manifestType: t(`manifestTypes.${labelKey}`) })}</span>{" "}
                <code>{reference.manifest_type}</code>
              </Link>
            </li>
          );
        })}
        <li><Link href={`/paper-jobs/${encodeURIComponent(descriptor.paper_jobs[0].job_id)}`}>{t("jobStep", { step: paperStep })}</Link></li>
        <li><Link href={`/portfolio-records/${encodeURIComponent(descriptor.paper_jobs[0].job_id)}`}>{t("portfolioStep", { step: paperStep + 1 })}</Link></li>
        <li><Link href={comparisonHref(descriptor.comparison_candidate_job_ids)}>{t("comparisonStep", { step: paperStep + 2 })}</Link></li>
        <li><Link href="/lifecycle-review">{t("lifecycleStep", { step: paperStep + 3 })}</Link></li>
        <li>
          <Link href={`/paper-accounts/${encodeURIComponent(descriptor.paper_account.account_id)}`}>
            {t("paperAccountStep", { step: paperStep + 4 })}
          </Link>
        </li>
      </ol>
      <p className="neutral-note">{t("demoBoundary")}</p>
    </section>
  );
}

export function FounderFirstRunPanel() {
  const t = useTranslations("overview.firstRun");
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
      const code = error instanceof ApiClientError ? error.code : null;
      setStandardState({
        status: "error",
        code,
        message: error instanceof ApiClientError ? error.publicMessage : null,
        requestId: error instanceof ApiClientError ? error.requestId : null,
        httpStatus: error instanceof ApiClientError && error.status > 0 ? error.status : null,
        operation: code?.startsWith("research_")
          ? "research_run.list"
          : code?.startsWith("evidence_")
            ? "evidence_manifest.list"
            : code?.startsWith("paper_") || code === "product_database_unavailable"
              ? "paper_job.list"
              : "unmatched",
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
    return <section className="first-run-panel" role="status"><p>{t("discovering")}</p></section>;
  }
  if (descriptorState.status === "success") {
    return <GuidedDemoJourney descriptor={descriptorState.data} />;
  }
  if (descriptorState.code !== "demo_workspace_not_configured") {
    return (
      <ErrorState
        className="first-run-panel"
        code={descriptorState.code}
        title={t("identityUnavailable")}
        message={descriptorState.message}
        requestId={descriptorState.requestId}
        httpStatus={descriptorState.httpStatus}
        operation="demo_workspace.read"
        onRetry={retryDescriptor}
        retryLabel={t("retryDiscovery")}
      />
    );
  }
  if (standardState.status === "loading") {
    return <section className="first-run-panel" role="status"><p>{t("checkingStandard")}</p></section>;
  }
  if (standardState.status === "error") {
    return (
      <ErrorState
        className="first-run-panel"
        code={standardState.code}
        title={t("dataUnavailableTitle")}
        message={standardState.message}
        requestId={standardState.requestId}
        httpStatus={standardState.httpStatus}
        operation={standardState.operation}
        onRetry={inspectStandard}
        retryLabel={t("retryEvidence")}
      />
    );
  }
  if (standardState.status === "populated") {
    return <section className="first-run-panel"><h2>{t("standardAvailableTitle")}</h2><p>{t("standardAvailableDescription")}</p></section>;
  }
  return (
    <section className="first-run-panel" aria-labelledby="empty-workspace-title">
      <p className="eyebrow">{t("emptyEyebrow")}</p>
      <h2 id="empty-workspace-title">{t("emptyTitle")}</h2>
      <p>{t("emptyDescription")}</p>
      <p>{t("emptyGuidance")}</p>
    </section>
  );
}
