"use client";

import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useCallback, useMemo, useState } from "react";

import { ErrorState } from "@/components/data-states";
import {
  PaperJobAttemptSummary,
  PaperJobStatusValue,
} from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import { StatusBadge, type StatusTone } from "@/components/ui/status-badge";
import { useWorkspaceEnvironment } from "@/components/workspace-shell";
import { useErrorPresentation } from "@/i18n/errors";
import {
  fetchEvidenceManifests,
  fetchEvidenceManifestDetail,
  fetchHealth,
  fetchPaperJobs,
  fetchPortfolioReviews,
  fetchResearchRuns,
  type DemoWorkspaceDescriptorResponse,
  type EvidenceManifestListResponse,
  type EvidenceManifestDetailResponse,
  type HealthResponse,
  type PaperJobListResponse,
  type PaperJobResponse,
  type PortfolioReviewListResponse,
  type ResearchRunListResponse,
} from "@/lib/api-client";
import {
  comparisonHref,
  comparisonSelectionErrorKey,
} from "@/lib/comparisons";
import {
  useApiResource,
  type ApiResourceState,
} from "@/lib/use-api-resource";

const DASHBOARD_JOB_LIMIT = 8;
const DASHBOARD_SOURCE_LIMIT = 5;

type Retry = () => number;

type AttentionItem = {
  key: string;
  titleKey:
    | "queued"
    | "failed"
    | "running"
    | "interrupted"
    | "result"
    | "emptyEvidence"
    | "dependency";
  rawValue: string;
  href: string | null;
  tone: StatusTone;
};

type Selection = {
  rowKey: string;
  jobId: string;
};

type ResultCandidate = {
  job: PaperJobResponse;
  sourceIndex: number;
  rowKey: string;
};

type ApiResourcePresentation<Data> = {
  evidence: ApiResourceState<Data>;
  initialLoading: boolean;
  refreshPending: boolean;
};

function apiResourcePresentation<Data>(
  state: ApiResourceState<Data>,
): ApiResourcePresentation<Data> {
  if (state.status !== "loading") {
    return {
      evidence: state,
      initialLoading: false,
      refreshPending: false,
    };
  }
  if (state.previous === null) {
    return {
      evidence: state,
      initialLoading: true,
      refreshPending: false,
    };
  }
  return {
    evidence: state.previous,
    initialLoading: false,
    refreshPending: true,
  };
}

function reconcileComparisonSelection(
  current: Selection[],
  candidates: readonly ResultCandidate[],
): Selection[] {
  const candidatesByRow = new Map(
    candidates.map((candidate) => [candidate.rowKey, candidate]),
  );
  const firstCandidateById = new Map<string, ResultCandidate>();
  candidates.forEach((candidate) => {
    if (
      candidate.job.job_id.trim().length > 0 &&
      !firstCandidateById.has(candidate.job.job_id)
    ) {
      firstCandidateById.set(candidate.job.job_id, candidate);
    }
  });

  const seenIds = new Set<string>();
  const reconciled: Selection[] = [];
  current.forEach((item) => {
    if (
      reconciled.length >= 4 ||
      item.jobId.trim().length === 0 ||
      seenIds.has(item.jobId)
    ) {
      return;
    }
    const exactRow = candidatesByRow.get(item.rowKey);
    const candidate =
      exactRow?.job.job_id === item.jobId
        ? exactRow
        : firstCandidateById.get(item.jobId);
    if (candidate === undefined) {
      return;
    }
    seenIds.add(item.jobId);
    reconciled.push({ rowKey: candidate.rowKey, jobId: item.jobId });
  });

  return reconciled.length === current.length &&
    reconciled.every(
      (item, index) =>
        item.rowKey === current[index]?.rowKey &&
        item.jobId === current[index]?.jobId,
    )
    ? current
    : reconciled;
}

function isStandardWorkspace(
  state: ApiResourceState<DemoWorkspaceDescriptorResponse>,
): boolean {
  return (
    state.status === "error" &&
    state.code === "demo_workspace_not_configured"
  );
}

function environmentDependencyState(
  state: ApiResourceState<DemoWorkspaceDescriptorResponse>,
): ApiResourceState<unknown> {
  if (
    state.status === "loading" &&
    state.previous !== null &&
    isStandardWorkspace(state.previous)
  ) {
    return {
      ...state,
      previous: {
        status: "success",
        data: null,
        requestId: state.previous.requestId,
        sequence: state.previous.sequence,
      },
    };
  }
  if (isStandardWorkspace(state) && state.status === "error") {
    return {
      status: "success",
      data: null,
      requestId: state.requestId,
      sequence: state.sequence,
    };
  }
  return state as ApiResourceState<unknown>;
}

function sourceCount(
  source:
    | ApiResourceState<ResearchRunListResponse>
    | ApiResourceState<EvidenceManifestListResponse>
    | ApiResourceState<PaperJobListResponse>
    | ApiResourceState<PortfolioReviewListResponse>,
): number | null {
  if (source.status !== "success") return null;
  if (Array.isArray(source.data)) return source.data.length;
  if ("runs" in source.data) return source.data.runs.length;
  return source.data.manifests.length;
}

function sourceStatus(
  state: ApiResourceState<unknown>,
  count: number | null,
): {
  key: "loading" | "empty" | "available" | "invalid" | "unavailable";
  tone: StatusTone;
} {
  if (state.status === "loading") return { key: "loading", tone: "info" };
  if (state.status === "error") {
    return state.code === "api_response_invalid"
      ? { key: "invalid", tone: "danger" }
      : { key: "unavailable", tone: "unavailable" };
  }
  return count === 0
    ? { key: "empty", tone: "neutral" }
    : { key: "available", tone: "success" };
}

function DashboardRegionHeader({
  eyebrow,
  title,
  description,
  id,
}: {
  eyebrow: string;
  title: string;
  description: string;
  id: string;
}) {
  return (
    <div className="section-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2 id={id}>{title}</h2>
      </div>
      <p>{description}</p>
    </div>
  );
}

function WorkspaceIdentityRegion({
  state,
  retry,
}: {
  state: ApiResourceState<DemoWorkspaceDescriptorResponse>;
  retry: Retry;
}) {
  const t = useTranslations("overview.dashboard.identity");
  const common = useTranslations("common");
  const locale = useLocale();
  const error = useErrorPresentation(
    state.status === "error" ? state.code : null,
  );

  return (
    <section
      className="dashboard-region dashboard-identity"
      aria-labelledby="dashboard-identity-title"
    >
      <DashboardRegionHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        id="dashboard-identity-title"
      />
      {state.status === "loading" ? (
        <div className="dashboard-state" role="status" aria-live="polite">
          <StatusBadge label={common("states.loading")} tone="info" />
          <p>{t("loading")}</p>
        </div>
      ) : state.status === "success" ? (
        <div className="workspace-identity-card workspace-identity-card--demo">
          <StatusBadge label={t("demo")} rawValue="demo" tone="demo" />
          <strong>{state.data.display_name}</strong>
          <p>{t("demoWarning")}</p>
          <dl className="compact-definitions">
            <div><dt>{t("dataset")}</dt><dd><code>{state.data.dataset_id}</code></dd></div>
            <div><dt>{t("version")}</dt><dd><code>{state.data.dataset_version}</code></dd></div>
            <div><dt>{t("locale")}</dt><dd><code>{locale}</code></dd></div>
          </dl>
        </div>
      ) : isStandardWorkspace(state) ? (
        <div className="workspace-identity-card">
          <StatusBadge label={t("standard")} rawValue="standard" tone="neutral" />
          <strong>{t("standardTitle")}</strong>
          <p>{t("standardDescription")}</p>
          <dl className="compact-definitions">
            <div><dt>{t("locale")}</dt><dd><code>{locale}</code></dd></div>
            <div><dt>{t("access")}</dt><dd>{t("founderOnly")}</dd></div>
          </dl>
        </div>
      ) : (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("unavailable") : error.title}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="demo_workspace.read"
          onRetry={retry}
          retryLabel={t("retry")}
        />
      )}
    </section>
  );
}

function ReadinessSource({
  label,
  endpoint,
  state,
  count,
  refreshPending,
  retry,
  processOnly = false,
  identityOnly = false,
}: {
  label: string;
  endpoint: string;
  state: ApiResourceState<unknown>;
  count: number | null;
  refreshPending: boolean;
  retry: Retry;
  processOnly?: boolean;
  identityOnly?: boolean;
}) {
  const t = useTranslations("overview.dashboard.readiness");
  const common = useTranslations("common");
  const status = sourceStatus(state, count);
  const error = useErrorPresentation(
    state.status === "error" ? state.code : null,
  );

  return (
    <li className="readiness-source" aria-busy={refreshPending}>
      <div className="readiness-source__heading">
        <div>
          <strong>{label}</strong>
          <code>{endpoint}</code>
        </div>
        <StatusBadge
          label={t(`states.${status.key}`)}
          rawValue={state.status === "error" ? state.code : undefined}
          tone={status.tone}
        />
      </div>
      {processOnly && state.status === "success" ? (
        <p>{t("processOnly")}</p>
      ) : identityOnly && state.status === "success" ? (
        <p>{t("identityResolved")}</p>
      ) : state.status === "success" ? (
        <p>{count === 0 ? t("emptySource") : t("availableSource", { count: count ?? 0 })}</p>
      ) : state.status === "loading" ? (
        <p role="status" aria-live="polite">{t("loadingSource")}</p>
      ) : (
        <>
          <p>{error.explanation}</p>
          <p>{error.recovery}</p>
          <details className="audit-disclosure">
            <summary>{common("backendDetail")}</summary>
            <p>{state.message}</p>
          </details>
        </>
      )}
      {refreshPending && state.status !== "loading" ? (
        <div
          className="readiness-source__pending"
          role="status"
          aria-live="polite"
        >
          <StatusBadge
            label={t(
              state.status === "error"
                ? "states.retrying"
                : "states.refreshing",
            )}
            tone="info"
          />
          <span>
            {t(
              state.status === "error"
                ? "retryInProgress"
                : "refreshInProgress",
              { source: label },
            )}
          </span>
        </div>
      ) : null}
      {state.status !== "loading" ? (
        <div className="readiness-source__actions">
          {state.requestId ? (
            <p className="request-id">{common("requestId", { requestId: state.requestId })}</p>
          ) : null}
          <button
            className="quiet-button"
            type="button"
            onClick={retry}
            disabled={refreshPending}
          >
            {refreshPending
              ? t(
                  state.status === "error"
                    ? "retryingSource"
                    : "refreshingSource",
                  { source: label },
                )
              : state.status === "error"
                ? t("retrySource", { source: label })
                : t("refreshSource", { source: label })}
          </button>
        </div>
      ) : null}
    </li>
  );
}

function ReadinessRegion({
  health,
  environment,
  research,
  evidence,
  jobs,
  reviews,
  retryHealth,
  retryEnvironment,
  retryResearch,
  retryEvidence,
  retryJobs,
  retryReviews,
}: {
  health: ApiResourceState<HealthResponse>;
  environment: ApiResourceState<DemoWorkspaceDescriptorResponse>;
  research: ApiResourceState<ResearchRunListResponse>;
  evidence: ApiResourceState<EvidenceManifestListResponse>;
  jobs: ApiResourceState<PaperJobListResponse>;
  reviews: ApiResourceState<PortfolioReviewListResponse>;
  retryHealth: Retry;
  retryEnvironment: Retry;
  retryResearch: Retry;
  retryEvidence: Retry;
  retryJobs: Retry;
  retryReviews: Retry;
}) {
  const t = useTranslations("overview.dashboard.readiness");
  const healthPresentation = apiResourcePresentation(health);
  const environmentPresentation = apiResourcePresentation(environment);
  const researchPresentation = apiResourcePresentation(research);
  const evidencePresentation = apiResourcePresentation(evidence);
  const jobsPresentation = apiResourcePresentation(jobs);
  const reviewsPresentation = apiResourcePresentation(reviews);
  const effectiveHealth = healthPresentation.evidence;
  const effectiveIdentity = environmentDependencyState(
    environmentPresentation.evidence,
  );
  const effectiveResearch = researchPresentation.evidence;
  const effectiveEvidence = evidencePresentation.evidence;
  const effectiveJobs = jobsPresentation.evidence;
  const effectiveReviews = reviewsPresentation.evidence;
  const sources = [
    effectiveHealth,
    effectiveIdentity,
    effectiveResearch,
    effectiveEvidence,
    effectiveJobs,
    effectiveReviews,
  ];
  const successCount = sources.filter((source) => source.status === "success").length;
  const errorCount = sources.filter((source) => source.status === "error").length;
  const unresolvedLoadingCount = sources.filter(
    (source) => source.status === "loading",
  ).length;
  const populated =
    (sourceCount(effectiveResearch) ?? 0) +
      (sourceCount(effectiveEvidence) ?? 0) +
      (sourceCount(effectiveJobs) ?? 0) +
      (sourceCount(effectiveReviews) ?? 0) >
    0;
  const healthUnavailable =
    effectiveHealth.status === "error" &&
    effectiveHealth.code === "api_unavailable";
  const summaryKey =
    errorCount > 0 && successCount > 0
      ? "partial"
      : errorCount > 0 && healthUnavailable
        ? "apiUnavailable"
        : errorCount > 0
          ? "unavailable"
          : unresolvedLoadingCount > 0
            ? "loading"
            : populated
              ? "populated"
              : "healthyEmpty";
  const summaryTone: StatusTone =
    summaryKey === "apiUnavailable" || summaryKey === "unavailable"
      ? "danger"
      : summaryKey === "partial"
        ? "warning"
        : summaryKey === "populated"
          ? "success"
          : summaryKey === "loading"
            ? "info"
            : "neutral";

  return (
    <section
      id="dashboard-readiness"
      className="dashboard-region"
      aria-labelledby="dashboard-readiness-title"
    >
      <DashboardRegionHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        id="dashboard-readiness-title"
      />
      <div className="readiness-summary" role="status" aria-live="polite">
        <StatusBadge label={t(`summary.${summaryKey}`)} tone={summaryTone} />
        <p>{t(`summaryDetail.${summaryKey}`)}</p>
      </div>
      <ul className="readiness-sources">
        <ReadinessSource
          label={t("sources.process")}
          endpoint="/api/v1/health"
          state={effectiveHealth}
          count={effectiveHealth.status === "success" ? 1 : null}
          refreshPending={healthPresentation.refreshPending}
          retry={retryHealth}
          processOnly
        />
        <ReadinessSource
          label={t("sources.identity")}
          endpoint="/api/v1/demo-workspace"
          state={effectiveIdentity}
          count={effectiveIdentity.status === "success" ? 1 : null}
          refreshPending={environmentPresentation.refreshPending}
          retry={retryEnvironment}
          identityOnly
        />
        <ReadinessSource
          label={t("sources.research")}
          endpoint="/api/v1/research-runs"
          state={effectiveResearch}
          count={sourceCount(effectiveResearch)}
          refreshPending={researchPresentation.refreshPending}
          retry={retryResearch}
        />
        <ReadinessSource
          label={t("sources.evidence")}
          endpoint="/api/v1/evidence-manifests"
          state={effectiveEvidence}
          count={sourceCount(effectiveEvidence)}
          refreshPending={evidencePresentation.refreshPending}
          retry={retryEvidence}
        />
        <ReadinessSource
          label={t("sources.jobs")}
          endpoint="/api/v1/paper-jobs"
          state={effectiveJobs}
          count={sourceCount(effectiveJobs)}
          refreshPending={jobsPresentation.refreshPending}
          retry={retryJobs}
        />
        <ReadinessSource
          label={t("sources.portfolioReviews")}
          endpoint="/api/v1/portfolio-reviews?limit=50"
          state={effectiveReviews}
          count={sourceCount(effectiveReviews)}
          refreshPending={reviewsPresentation.refreshPending}
          retry={retryReviews}
        />
      </ul>
    </section>
  );
}

function buildAttentionItems({
  health,
  environment,
  research,
  evidence,
  jobs,
}: {
  health: ApiResourceState<HealthResponse>;
  environment: ApiResourceState<DemoWorkspaceDescriptorResponse>;
  research: ApiResourceState<ResearchRunListResponse>;
  evidence: ApiResourceState<EvidenceManifestListResponse>;
  jobs: ApiResourceState<PaperJobListResponse>;
}): AttentionItem[] {
  const items: AttentionItem[] = [];
  if (
    environment.status === "error" &&
    environment.code !== "demo_workspace_not_configured"
  ) {
    items.push({
      key: "dependency-identity",
      titleKey: "dependency",
      rawValue: environment.code,
      href: "#dashboard-readiness",
      tone:
        environment.code === "api_response_invalid" ? "danger" : "unavailable",
    });
  }
  for (const [name, source] of [
    ["health", health],
    ["research", research],
    ["evidence", evidence],
    ["jobs", jobs],
  ] as const) {
    if (source.status === "error") {
      items.push({
        key: `dependency-${name}`,
        titleKey: "dependency",
        rawValue: source.code,
        href: "#dashboard-readiness",
        tone: source.code === "api_response_invalid" ? "danger" : "unavailable",
      });
    }
  }
  if (jobs.status === "success") {
    jobs.data.forEach((job, index) => {
      const base = {
        key: `${job.job_id}-${index}`,
        rawValue: `${job.job_id} · ${job.status}`,
        href: `/paper-jobs/${encodeURIComponent(job.job_id)}`,
      };
      if (job.status === "queued") {
        items.push({ ...base, titleKey: "queued", tone: "info" });
      } else if (job.status === "failed") {
        items.push({ ...base, titleKey: "failed", tone: "danger" });
      } else if (
        job.status === "running" &&
        job.latest_attempt?.status === "interrupted"
      ) {
        items.push({ ...base, titleKey: "interrupted", tone: "warning" });
      } else if (job.status === "running") {
        items.push({ ...base, titleKey: "running", tone: "warning" });
      } else if (job.status === "succeeded" && job.result_available) {
        items.push({
          ...base,
          titleKey: "result",
          href: `/portfolio-records/${encodeURIComponent(job.job_id)}`,
          tone: "success",
        });
      }
    });
  }
  if (
    health.status === "success" &&
    research.status === "success" &&
    evidence.status === "success" &&
    jobs.status === "success" &&
    research.data.runs.length === 0 &&
    evidence.data.manifests.length === 0
  ) {
    items.push({
      key: "empty-evidence",
      titleKey: "emptyEvidence",
      rawValue: "research=0 · evidence=0",
      href: "/research-runs",
      tone: "neutral",
    });
  }
  return items;
}

function AttentionRegion({
  health,
  environment,
  research,
  evidence,
  jobs,
}: {
  health: ApiResourceState<HealthResponse>;
  environment: ApiResourceState<DemoWorkspaceDescriptorResponse>;
  research: ApiResourceState<ResearchRunListResponse>;
  evidence: ApiResourceState<EvidenceManifestListResponse>;
  jobs: ApiResourceState<PaperJobListResponse>;
}) {
  const t = useTranslations("overview.dashboard.attention");
  const healthPresentation = apiResourcePresentation(health);
  const environmentPresentation = apiResourcePresentation(environment);
  const researchPresentation = apiResourcePresentation(research);
  const evidencePresentation = apiResourcePresentation(evidence);
  const jobsPresentation = apiResourcePresentation(jobs);
  const presentations = [
    healthPresentation,
    environmentPresentation,
    researchPresentation,
    evidencePresentation,
    jobsPresentation,
  ];
  const items = buildAttentionItems({
    health: healthPresentation.evidence,
    environment: environmentPresentation.evidence,
    research: researchPresentation.evidence,
    evidence: evidencePresentation.evidence,
    jobs: jobsPresentation.evidence,
  });
  const anyInitialLoading = presentations.some(
    (presentation) => presentation.initialLoading,
  );
  const anyRefreshPending = presentations.some(
    (presentation) => presentation.refreshPending,
  );

  return (
    <section
      className="dashboard-region"
      aria-labelledby="dashboard-attention-title"
    >
      <DashboardRegionHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        id="dashboard-attention-title"
      />
      {items.length === 0 && anyInitialLoading ? (
        <div className="dashboard-state" role="status" aria-live="polite">
          <p>{t("loading")}</p>
        </div>
      ) : items.length === 0 ? (
        <div className="dashboard-state dashboard-state--empty">
          <p>{t("empty")}</p>
        </div>
      ) : (
        <ul className="attention-list">
          {items.map((item) => (
            <li key={item.key}>
              <StatusBadge
                label={t(`items.${item.titleKey}`)}
                rawValue={item.rawValue}
                tone={item.tone}
              />
              <p>{t(`details.${item.titleKey}`)}</p>
              {item.href ? (
                <Link className="text-link" href={item.href}>
                  {t("inspect")}
                </Link>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      {anyRefreshPending ? (
        <p className="attention-refresh-note">{t("refreshPending")}</p>
      ) : null}
      <p className="neutral-note">{t("boundary")}</p>
    </section>
  );
}

function JobSummary({ job }: { job: PaperJobResponse }) {
  const t = useTranslations("overview.dashboard.jobs");
  const common = useTranslations("common.states");
  return (
    <li className="dashboard-job-card">
      <div className="dashboard-job-card__heading">
        <div>
          <code>{job.job_id}</code>
          <h3>{job.run_id}</h3>
        </div>
        <PaperJobStatusValue value={job.status} />
      </div>
      <dl className="dashboard-definitions">
        <div><dt>{t("submitted")}</dt><dd><LocalizedTimestamp value={job.submitted_timestamp} /></dd></div>
        <div><dt>{t("updated")}</dt><dd><LocalizedTimestamp value={job.updated_timestamp} /></dd></div>
        <div><dt>{t("latestAttempt")}</dt><dd>{job.latest_attempt ? <PaperJobAttemptSummary attemptNumber={job.latest_attempt.attempt_number} status={job.latest_attempt.status} /> : common("notAvailable")}</dd></div>
        <div><dt>{t("result")}</dt><dd>{job.result_available ? common("yes") : common("no")}</dd></div>
      </dl>
      <div className="record-card__actions">
        <Link className="primary-link" href={`/paper-jobs/${encodeURIComponent(job.job_id)}`}>
          {t("inspectJob")}
        </Link>
        {job.result_available ? (
          <Link className="text-link" href={`/portfolio-records/${encodeURIComponent(job.job_id)}`}>
            {t("inspectResult")}
          </Link>
        ) : null}
      </div>
    </li>
  );
}

function PaperActivityRegion({
  state,
  retry,
}: {
  state: ApiResourceState<PaperJobListResponse>;
  retry: Retry;
}) {
  const t = useTranslations("overview.dashboard.jobs");
  const error = useErrorPresentation(
    state.status === "error" ? state.code : null,
  );
  return (
    <section
      className="dashboard-region"
      aria-labelledby="dashboard-jobs-title"
    >
      <DashboardRegionHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        id="dashboard-jobs-title"
      />
      {state.status === "loading" ? (
        <div className="dashboard-state" role="status" aria-live="polite">
          <p>{t("loading")}</p>
        </div>
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("unavailable") : error.title}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="paper_job.list"
          onRetry={retry}
          retryLabel={t("retry")}
        />
      ) : state.data.length === 0 ? (
        <div className="dashboard-state dashboard-state--empty">
          <p>{t("empty")}</p>
          <Link className="text-link" href="/paper-jobs/new">{t("submit")}</Link>
        </div>
      ) : (
        <ol className="dashboard-job-list" aria-label={t("ariaLabel")}>
          {state.data.map((job, index) => (
            <JobSummary key={`${job.job_id}-${index}`} job={job} />
          ))}
        </ol>
      )}
      <div className="dashboard-region__footer">
        <Link className="text-link" href="/paper-jobs">{t("allJobs")}</Link>
        {state.status === "success" ? (
          <button className="quiet-button" type="button" onClick={retry}>{t("refresh")}</button>
        ) : null}
      </div>
    </section>
  );
}

function ResultsRegion({
  state,
  retry,
}: {
  state: ApiResourceState<PaperJobListResponse>;
  retry: Retry;
}) {
  const t = useTranslations("overview.dashboard.results");
  const comparisonErrors = useTranslations("comparisons.selectionErrors");
  const error = useErrorPresentation(
    state.status === "error" ? state.code : null,
  );
  const [selectionState, setSelectionState] = useState<{
    items: Selection[];
    sourceSequence: number | null;
  }>({ items: [], sourceSequence: null });
  const selection = selectionState.items;
  const candidates = useMemo<ResultCandidate[]>(
    () =>
      state.status === "success"
        ? state.data
            .map((job, sourceIndex) => ({
              job,
              sourceIndex,
              rowKey: `${sourceIndex}:${job.job_id}`,
            }))
            .filter(({ job }) => job.result_available)
        : [],
    [state],
  );
  const reconciledSelection =
    state.status === "success"
      ? reconcileComparisonSelection(selection, candidates)
      : selection;
  if (
    state.status === "success" &&
    selectionState.sourceSequence !== state.sequence
  ) {
    setSelectionState({
      items: reconciledSelection,
      sourceSequence: state.sequence,
    });
  }
  const selectedIds = reconciledSelection.map((item) => item.jobId);
  const selectionError = comparisonSelectionErrorKey(selectedIds);
  const comparisonReady =
    selectedIds.length >= 2 && selectionError === null;

  return (
    <section
      className="dashboard-region"
      aria-labelledby="dashboard-results-title"
    >
      <DashboardRegionHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        id="dashboard-results-title"
      />
      {state.status === "loading" ? (
        <div className="dashboard-state" role="status" aria-live="polite"><p>{t("loading")}</p></div>
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("unavailable") : error.title}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="paper_job.list"
          onRetry={retry}
          retryLabel={t("retry")}
        />
      ) : candidates.length === 0 ? (
        <div className="dashboard-state dashboard-state--empty">
          <p>{t("empty")}</p>
          <Link className="text-link" href="/portfolio-records">{t("browse")}</Link>
        </div>
      ) : (
        <>
          <fieldset className="comparison-selection">
            <legend>{t("legend")}</legend>
            <p>{t("helper")}</p>
            <ul>
              {candidates.map(({ job, sourceIndex }) => {
                const rowKey = `${sourceIndex}:${job.job_id}`;
                const checked = reconciledSelection.some(
                  (item) => item.rowKey === rowKey,
                );
                const selectedOnDuplicateRow = reconciledSelection.some(
                  (item) =>
                    item.jobId === job.job_id && item.rowKey !== rowKey,
                );
                const blankId = job.job_id.trim().length === 0;
                const maximumReached = reconciledSelection.length >= 4;
                const disabled =
                  !checked &&
                  (blankId || selectedOnDuplicateRow || maximumReached);
                const constraintKey = blankId
                  ? "blankUnavailable"
                  : selectedOnDuplicateRow
                    ? "duplicateSelected"
                    : maximumReached
                      ? "maximumSelected"
                      : null;
                const constraintId =
                  constraintKey === null
                    ? undefined
                    : `comparison-constraint-${sourceIndex}`;
                return (
                  <li key={rowKey}>
                    <div className="comparison-selection__choice">
                      <label>
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={disabled}
                          aria-describedby={constraintId}
                          onChange={(event) => {
                            setSelectionState((current) => {
                              const validCurrent =
                                reconcileComparisonSelection(
                                  current.items,
                                  candidates,
                                );
                              if (!event.target.checked) {
                                return {
                                  items: validCurrent.filter(
                                    (item) => item.rowKey !== rowKey,
                                  ),
                                  sourceSequence: state.sequence,
                                };
                              }
                              if (
                                job.job_id.trim().length === 0 ||
                                validCurrent.length >= 4 ||
                                validCurrent.some(
                                  (item) => item.jobId === job.job_id,
                                )
                              ) {
                                return {
                                  items: validCurrent,
                                  sourceSequence: state.sequence,
                                };
                              }
                              return {
                                items: [
                                  ...validCurrent,
                                  { rowKey, jobId: job.job_id },
                                ],
                                sourceSequence: state.sequence,
                              };
                            });
                          }}
                        />
                        <span><code>{job.job_id}</code> · <code>{job.run_id}</code></span>
                      </label>
                      {constraintKey === null ? null : (
                        <span
                          className="comparison-selection__constraint"
                          id={constraintId}
                        >
                          {t(constraintKey, { jobId: job.job_id })}
                        </span>
                      )}
                    </div>
                    <Link className="text-link" href={`/portfolio-records/${encodeURIComponent(job.job_id)}`}>
                      {t("inspect")}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </fieldset>
          <div className="comparison-selection__summary" aria-live="polite">
            <p>{t("selected", { count: reconciledSelection.length })}</p>
            {reconciledSelection.length > 0 ? (
              <ol aria-label={t("selectionOrder")}>
                {reconciledSelection.map((item, index) => (
                  <li key={`${item.rowKey}-${index}`}><code>{item.jobId}</code></li>
                ))}
              </ol>
            ) : null}
            {comparisonReady ? (
              <Link className="primary-link" href={comparisonHref(selectedIds)}>
                {t("compare")}
              </Link>
            ) : (
              <span className="disabled-action" aria-disabled="true">
                {selectionError === null
                  ? t("chooseTwo")
                  : comparisonErrors(selectionError)}
              </span>
            )}
          </div>
        </>
      )}
      <p className="neutral-note">{t("boundary")}</p>
    </section>
  );
}

function ResearchRegion({
  state,
  retry,
}: {
  state: ApiResourceState<ResearchRunListResponse>;
  retry: Retry;
}) {
  const t = useTranslations("overview.dashboard.research");
  const error = useErrorPresentation(
    state.status === "error" ? state.code : null,
  );
  return (
    <section className="dashboard-region" aria-labelledby="dashboard-research-title">
      <DashboardRegionHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        id="dashboard-research-title"
      />
      {state.status === "loading" ? (
        <div className="dashboard-state" role="status"><p>{t("loading")}</p></div>
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("unavailable") : error.title}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="research_run.list"
          onRetry={retry}
          retryLabel={t("retry")}
        />
      ) : state.data.runs.length === 0 ? (
        <div className="dashboard-state dashboard-state--empty"><p>{t("empty")}</p></div>
      ) : (
        <ol className="dashboard-source-list" aria-label={t("ariaLabel")}>
          {state.data.runs.slice(0, DASHBOARD_SOURCE_LIMIT).map((run, index) => (
            <li key={`${run.experiment_slug}-${run.run_id}-${index}`}>
              <div>
                <strong>{run.experiment_name}</strong>
                <code>{run.experiment_slug} / {run.run_id}</code>
                <span>{run.strategy} · {run.data_source}</span>
              </div>
              <Link className="text-link" href={`/research-runs/${encodeURIComponent(run.experiment_slug)}/${encodeURIComponent(run.run_id)}`}>
                {t("inspect")}
              </Link>
            </li>
          ))}
        </ol>
      )}
      <div className="dashboard-region__footer">
        <Link className="text-link" href="/research-runs">{t("browse")}</Link>
        {state.status === "success" ? <button className="quiet-button" type="button" onClick={retry}>{t("refresh")}</button> : null}
      </div>
    </section>
  );
}

function EvidenceRegion({
  state,
  retry,
}: {
  state: ApiResourceState<EvidenceManifestListResponse>;
  retry: Retry;
}) {
  const t = useTranslations("overview.dashboard.evidence");
  const error = useErrorPresentation(
    state.status === "error" ? state.code : null,
  );
  return (
    <section className="dashboard-region" aria-labelledby="dashboard-evidence-title">
      <DashboardRegionHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        id="dashboard-evidence-title"
      />
      {state.status === "loading" ? (
        <div className="dashboard-state" role="status"><p>{t("loading")}</p></div>
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("unavailable") : error.title}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="evidence_manifest.list"
          onRetry={retry}
          retryLabel={t("retry")}
        />
      ) : state.data.manifests.length === 0 ? (
        <div className="dashboard-state dashboard-state--empty"><p>{t("empty")}</p></div>
      ) : (
        <ol className="dashboard-source-list" aria-label={t("ariaLabel")}>
          {state.data.manifests
            .slice(0, DASHBOARD_SOURCE_LIMIT)
            .map((manifest, index) => (
              <EvidenceManifestCard
                key={`${manifest.manifest_type}-${manifest.artifact_key}-${index}`}
                manifest={manifest}
              />
            ))}
        </ol>
      )}
      <div className="dashboard-region__footer">
        <Link className="text-link" href="/evidence-manifests">{t("browse")}</Link>
        {state.status === "success" ? <button className="quiet-button" type="button" onClick={retry}>{t("refresh")}</button> : null}
      </div>
    </section>
  );
}

function EvidenceManifestCard({
  manifest,
}: {
  manifest: EvidenceManifestListResponse["manifests"][number];
}) {
  const t = useTranslations("overview.dashboard.evidence");
  const common = useTranslations("common");
  const request = useCallback(
    (): Promise<{
      data: EvidenceManifestDetailResponse;
      requestId: string | null;
    }> =>
      fetchEvidenceManifestDetail(
        manifest.manifest_type,
        manifest.artifact_key,
      ),
    [manifest.artifact_key, manifest.manifest_type],
  );
  const detail = useApiResource(request);
  const detailError = useErrorPresentation(
    detail.state.status === "error" ? detail.state.code : null,
  );

  return (
    <li>
      <div>
        <strong>{manifest.label ?? manifest.manifest_id}</strong>
        <dl className="dashboard-definitions dashboard-source-definitions">
          <div>
            <dt>{t("manifestId")}</dt>
            <dd><code>{manifest.manifest_id}</code></dd>
          </div>
          <div>
            <dt>{t("schemaVersion")}</dt>
            <dd>
              {detail.state.status === "loading" ? (
                <span role="status" aria-live="polite">{t("schemaLoading")}</span>
              ) : detail.state.status === "error" ? (
                <span className="dashboard-source-value-state">
                  <code>{common("errorCode", { code: detail.state.code })}</code>
                  <span>{detailError.explanation}</span>
                  <span>{detailError.recovery}</span>
                  {detail.state.requestId ? (
                    <code>{common("requestId", { requestId: detail.state.requestId })}</code>
                  ) : null}
                  <button
                    className="quiet-button"
                    type="button"
                    onClick={detail.retry}
                  >
                    {t("retrySchema")}
                  </button>
                </span>
              ) : (
                <code>{detail.state.data.schema_version}</code>
              )}
            </dd>
          </div>
          <div>
            <dt>{t("manifestType")}</dt>
            <dd><code>{manifest.manifest_type}</code></dd>
          </div>
          <div>
            <dt>{t("artifactKey")}</dt>
            <dd><code>{manifest.artifact_key}</code></dd>
          </div>
          <div>
            <dt>{t("referenceCount")}</dt>
            <dd>{t("references", { count: manifest.reference_count })}</dd>
          </div>
        </dl>
      </div>
      <Link
        className="text-link"
        href={`/evidence-manifests/${encodeURIComponent(manifest.manifest_type)}/${encodeURIComponent(manifest.artifact_key)}`}
      >
        {t("inspect")}
      </Link>
    </li>
  );
}

function DemoWorkflow({
  descriptor,
}: {
  descriptor: DemoWorkspaceDescriptorResponse;
}) {
  const t = useTranslations("overview.dashboard.workflow");
  const evidenceStart = 3;
  const paperStart = evidenceStart + descriptor.evidence_manifests.length;
  const comparisonStep = paperStart + descriptor.paper_jobs.length * 2;
  return (
    <>
      <ol className="dashboard-workflow">
        <li>
          <Link href={`/strategies/${encodeURIComponent(descriptor.canonical_strategy_name)}`}>
            <span>{t("demo.strategy", { step: 1 })}</span>
            <code>{descriptor.canonical_strategy_name}</code>
          </Link>
        </li>
        <li>
          <Link href={`/research-runs/${encodeURIComponent(descriptor.research_run.experiment_slug)}/${encodeURIComponent(descriptor.research_run.run_id)}`}>
            <span>{t("demo.research", { step: 2 })}</span>
            <code>{descriptor.research_run.experiment_slug} / {descriptor.research_run.run_id}</code>
          </Link>
        </li>
        {descriptor.evidence_manifests.map((manifest, index) => (
          <li key={`${manifest.manifest_type}-${manifest.artifact_key}-${index}`}>
            <Link href={`/evidence-manifests/${encodeURIComponent(manifest.manifest_type)}/${encodeURIComponent(manifest.artifact_key)}`}>
              <span>{t("demo.evidence", { step: evidenceStart + index })}</span>
              <code>{manifest.manifest_type} / {manifest.artifact_key}</code>
            </Link>
          </li>
        ))}
        {descriptor.paper_jobs.flatMap((job, index) => {
          const jobStep = paperStart + index * 2;
          return [
            <li key={`job-${job.job_id}-${index}`}>
              <Link href={`/paper-jobs/${encodeURIComponent(job.job_id)}`}>
                <span>{t("demo.job", { step: jobStep })}</span>
                <code>{job.job_id} / {job.run_id}</code>
              </Link>
            </li>,
            <li key={`result-${job.job_id}-${index}`}>
              <Link href={`/portfolio-records/${encodeURIComponent(job.job_id)}`}>
                <span>{t("demo.result", { step: jobStep + 1 })}</span>
                <code>{job.job_id}</code>
              </Link>
            </li>,
          ];
        })}
        <li>
          <Link href={comparisonHref(descriptor.comparison_candidate_job_ids)}>
            <span>{t("demo.comparison", { step: comparisonStep })}</span>
            <code>{descriptor.comparison_candidate_job_ids.join(" → ")}</code>
          </Link>
        </li>
        <li>
          <Link href={`/portfolio-reviews/${encodeURIComponent(descriptor.portfolio_review_example.request.review_id)}`}>
            <span>{t("demo.portfolioReview", { step: comparisonStep + 1 })}</span>
            <code>{descriptor.portfolio_review_example.request.review_id}</code>
          </Link>
        </li>
        <li>
          <Link href="/lifecycle-review">
            <span>{t("demo.lifecycle", { step: comparisonStep + 2 })}</span>
            <code>{descriptor.lifecycle_proposal_example.proposal_id}</code>
          </Link>
        </li>
      </ol>
      <details className="audit-disclosure">
        <summary>{t("demo.audit")}</summary>
        <dl className="dashboard-definitions">
          <div><dt>{t("demo.proposal")}</dt><dd><code>{descriptor.lifecycle_proposal_example.proposal_id}</code></dd></div>
          <div><dt>{t("demo.humanDecision")}</dt><dd><code>{descriptor.lifecycle_review_example.transition_record_id}</code></dd></div>
          <div><dt>{t("demo.submission")}</dt><dd><code>{descriptor.paper_job_submission_example.idempotency_key}</code></dd></div>
        </dl>
      </details>
    </>
  );
}

function WorkflowRegion({
  state,
  retry,
}: {
  state: ApiResourceState<DemoWorkspaceDescriptorResponse>;
  retry: Retry;
}) {
  const t = useTranslations("overview.dashboard.workflow");
  const error = useErrorPresentation(
    state.status === "error" ? state.code : null,
  );
  const standard = isStandardWorkspace(state);
  return (
    <section className="dashboard-region dashboard-region--wide" aria-labelledby="dashboard-workflow-title">
      <DashboardRegionHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        id="dashboard-workflow-title"
      />
      {state.status === "loading" ? (
        <div className="dashboard-state" role="status"><p>{t("loading")}</p></div>
      ) : state.status === "success" ? (
        <DemoWorkflow descriptor={state.data} />
      ) : standard ? (
        <>
          <p className="neutral-note">{t("standardBoundary")}</p>
          <ol className="dashboard-workflow dashboard-workflow--standard">
            {([
              ["/strategies", "standard.strategies"],
              ["/research-runs", "standard.research"],
              ["/evidence-manifests", "standard.evidence"],
              ["/paper-jobs", "standard.jobs"],
              ["/portfolio-records", "standard.results"],
              ["/comparisons", "standard.comparison"],
              ["/portfolio-reviews", "standard.portfolioReviews"],
              ["/lifecycle-review", "standard.lifecycle"],
            ] as const).map(([href, key], index) => (
              <li key={href}>
                <Link href={href}>
                  <span>{t(key, { step: index + 1 })}</span>
                </Link>
              </li>
            ))}
          </ol>
        </>
      ) : (
        <ErrorState
          code={state.code}
          title={error.useContextTitle ? t("unavailable") : error.title}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="demo_workspace.read"
          onRetry={retry}
          retryLabel={t("retry")}
        />
      )}
      <p className="neutral-note">{t("commandBoundary")}</p>
    </section>
  );
}

function TechnicalRegion({
  sources,
}: {
  sources: readonly {
    label: string;
    endpoint: string;
    state: ApiResourceState<unknown>;
    retry: Retry;
  }[];
}) {
  const t = useTranslations("overview.dashboard.technical");
  const readiness = useTranslations("overview.dashboard.readiness");
  const common = useTranslations("common");
  return (
    <section className="dashboard-region dashboard-region--wide" aria-labelledby="dashboard-technical-title">
      <DashboardRegionHeader
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t("description")}
        id="dashboard-technical-title"
      />
      <ul className="technical-source-list">
        {sources.map((source) => {
          const presentation = apiResourcePresentation(source.state);
          const evidence = presentation.evidence;
          return (
            <li
              key={source.endpoint}
              aria-busy={
                presentation.initialLoading || presentation.refreshPending
              }
            >
              <div>
                <strong>{source.label}</strong>
                <code>{source.endpoint}</code>
                {evidence.status === "error" ? (
                  <>
                    <span>{common("errorCode", { code: evidence.code })}</span>
                    {evidence.requestId ? (
                      <span>
                        {common("requestId", {
                          requestId: evidence.requestId,
                        })}
                      </span>
                    ) : null}
                  </>
                ) : evidence.status === "success" && evidence.requestId ? (
                  <span>
                    {common("requestId", {
                      requestId: evidence.requestId,
                    })}
                  </span>
                ) : null}
                {presentation.refreshPending &&
                evidence.status !== "loading" ? (
                  <span className="technical-source__pending">
                    {readiness(
                      evidence.status === "error"
                        ? "retryInProgress"
                        : "refreshInProgress",
                      { source: source.label },
                    )
                    }
                  </span>
                ) : null}
              </div>
              <button
                className="quiet-button"
                type="button"
                onClick={source.retry}
                disabled={
                  presentation.initialLoading || presentation.refreshPending
                }
              >
                {presentation.initialLoading
                  ? t("loading")
                  : presentation.refreshPending &&
                      evidence.status !== "loading"
                    ? readiness(
                        evidence.status === "error"
                          ? "retryingSource"
                          : "refreshingSource",
                        { source: source.label },
                      )
                    : t("refresh", { source: source.label })}
              </button>
            </li>
          );
        })}
      </ul>
      <p className="neutral-note">{t("boundary")}</p>
    </section>
  );
}

export function FounderDashboard() {
  const t = useTranslations("overview.dashboard");
  const environment = useWorkspaceEnvironment();
  const healthRequest = useCallback(() => fetchHealth(), []);
  const researchRequest = useCallback(() => fetchResearchRuns(), []);
  const evidenceRequest = useCallback(() => fetchEvidenceManifests(), []);
  const jobsRequest = useCallback(
    () => fetchPaperJobs({ status: null, limit: DASHBOARD_JOB_LIMIT }),
    [],
  );
  const reviewsRequest = useCallback(
    () => fetchPortfolioReviews({ status: null, limit: 50 }),
    [],
  );
  const health = useApiResource(healthRequest);
  const research = useApiResource(researchRequest);
  const evidence = useApiResource(evidenceRequest);
  const jobs = useApiResource(jobsRequest);
  const reviews = useApiResource(reviewsRequest);
  const technicalSources = useMemo(
    () => [
      {
        label: t("technical.sources.identity"),
        endpoint: "/api/v1/demo-workspace",
        state: environmentDependencyState(environment.state),
        retry: environment.retry,
      },
      {
        label: t("technical.sources.process"),
        endpoint: "/api/v1/health",
        state: health.state as ApiResourceState<unknown>,
        retry: health.retry,
      },
      {
        label: t("technical.sources.research"),
        endpoint: "/api/v1/research-runs",
        state: research.state as ApiResourceState<unknown>,
        retry: research.retry,
      },
      {
        label: t("technical.sources.evidence"),
        endpoint: "/api/v1/evidence-manifests",
        state: evidence.state as ApiResourceState<unknown>,
        retry: evidence.retry,
      },
      {
        label: t("technical.sources.jobs"),
        endpoint: `/api/v1/paper-jobs?limit=${DASHBOARD_JOB_LIMIT}`,
        state: jobs.state as ApiResourceState<unknown>,
        retry: jobs.retry,
      },
      {
        label: t("technical.sources.portfolioReviews"),
        endpoint: "/api/v1/portfolio-reviews?limit=50",
        state: reviews.state as ApiResourceState<unknown>,
        retry: reviews.retry,
      },
    ],
    [
      environment.retry,
      environment.state,
      evidence.retry,
      evidence.state,
      health.retry,
      health.state,
      jobs.retry,
      jobs.state,
      research.retry,
      research.state,
      reviews.retry,
      reviews.state,
      t,
    ],
  );

  return (
    <div className="overview founder-dashboard">
      <header className="overview-hero">
        <p className="eyebrow">{t("hero.eyebrow")}</p>
        <h1>{t("hero.title")}</h1>
        <p className="overview-hero__summary">{t("hero.summary")}</p>
        <div className="overview-actions">
          <Link className="primary-link" href="/paper-jobs">{t("hero.paperJobs")}</Link>
          <Link className="text-link" href="/research-runs">{t("hero.research")}</Link>
          <Link className="text-link" href="/lifecycle-review">{t("hero.lifecycle")}</Link>
        </div>
      </header>

      <div className="dashboard-grid">
        <WorkspaceIdentityRegion state={environment.state} retry={environment.retry} />
        <ReadinessRegion
          health={health.state}
          environment={environment.state}
          research={research.state}
          evidence={evidence.state}
          jobs={jobs.state}
          reviews={reviews.state}
          retryHealth={health.retry}
          retryEnvironment={environment.retry}
          retryResearch={research.retry}
          retryEvidence={evidence.retry}
          retryJobs={jobs.retry}
          retryReviews={reviews.retry}
        />
        <AttentionRegion
          health={health.state}
          environment={environment.state}
          research={research.state}
          evidence={evidence.state}
          jobs={jobs.state}
        />
        <PaperActivityRegion state={jobs.state} retry={jobs.retry} />
        <ResultsRegion state={jobs.state} retry={jobs.retry} />
        <ResearchRegion state={research.state} retry={research.retry} />
        <EvidenceRegion state={evidence.state} retry={evidence.retry} />
        <WorkflowRegion state={environment.state} retry={environment.retry} />
        <TechnicalRegion sources={technicalSources} />
      </div>
    </div>
  );
}
