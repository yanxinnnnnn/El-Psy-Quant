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
  fetchHealth,
  fetchPaperJobs,
  fetchResearchRuns,
  type DemoWorkspaceDescriptorResponse,
  type EvidenceManifestListResponse,
  type HealthResponse,
  type PaperJobListResponse,
  type PaperJobResponse,
  type ResearchRunListResponse,
} from "@/lib/api-client";
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

function comparisonHref(jobIds: readonly string[]): string {
  const query = new URLSearchParams();
  jobIds.forEach((jobId) => query.append("job_id", jobId));
  return `/comparisons?${query.toString()}`;
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
    | ApiResourceState<PaperJobListResponse>,
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
  retry,
  processOnly = false,
  identityOnly = false,
}: {
  label: string;
  endpoint: string;
  state: ApiResourceState<unknown>;
  count: number | null;
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
    <li className="readiness-source">
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
      {state.status !== "loading" ? (
        <div className="readiness-source__actions">
          {state.requestId ? (
            <p className="request-id">{common("requestId", { requestId: state.requestId })}</p>
          ) : null}
          <button className="quiet-button" type="button" onClick={retry}>
            {state.status === "error" ? t("retrySource", { source: label }) : t("refreshSource", { source: label })}
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
  retryHealth,
  retryEnvironment,
  retryResearch,
  retryEvidence,
  retryJobs,
}: {
  health: ApiResourceState<HealthResponse>;
  environment: ApiResourceState<DemoWorkspaceDescriptorResponse>;
  research: ApiResourceState<ResearchRunListResponse>;
  evidence: ApiResourceState<EvidenceManifestListResponse>;
  jobs: ApiResourceState<PaperJobListResponse>;
  retryHealth: Retry;
  retryEnvironment: Retry;
  retryResearch: Retry;
  retryEvidence: Retry;
  retryJobs: Retry;
}) {
  const t = useTranslations("overview.dashboard.readiness");
  const identity = environmentDependencyState(environment);
  const sources = [identity, research, evidence, jobs];
  const successCount = sources.filter((source) => source.status === "success").length;
  const errorCount = sources.filter((source) => source.status === "error").length;
  const loadingCount = sources.filter((source) => source.status === "loading").length;
  const populated =
    (sourceCount(research) ?? 0) +
      (sourceCount(evidence) ?? 0) +
      (sourceCount(jobs) ?? 0) >
    0;
  const summaryKey =
    health.status === "error"
      ? "apiUnavailable"
      : errorCount > 0 && successCount > 0
        ? "partial"
        : errorCount > 0
          ? "unavailable"
          : loadingCount > 0 || health.status === "loading"
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
          state={health}
          count={health.status === "success" ? 1 : null}
          retry={retryHealth}
          processOnly
        />
        <ReadinessSource
          label={t("sources.identity")}
          endpoint="/api/v1/demo-workspace"
          state={identity}
          count={identity.status === "success" ? 1 : null}
          retry={retryEnvironment}
          identityOnly
        />
        <ReadinessSource
          label={t("sources.research")}
          endpoint="/api/v1/research-runs"
          state={research}
          count={sourceCount(research)}
          retry={retryResearch}
        />
        <ReadinessSource
          label={t("sources.evidence")}
          endpoint="/api/v1/evidence-manifests"
          state={evidence}
          count={sourceCount(evidence)}
          retry={retryEvidence}
        />
        <ReadinessSource
          label={t("sources.jobs")}
          endpoint="/api/v1/paper-jobs"
          state={jobs}
          count={sourceCount(jobs)}
          retry={retryJobs}
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
  const items = buildAttentionItems({ health, environment, research, evidence, jobs });
  const anyLoading = [health, environment, research, evidence, jobs].some(
    (source) => source.status === "loading",
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
      {items.length === 0 && anyLoading ? (
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
  const error = useErrorPresentation(
    state.status === "error" ? state.code : null,
  );
  const [selection, setSelection] = useState<Selection[]>([]);
  const candidates =
    state.status === "success"
      ? state.data
          .map((job, sourceIndex) => ({ job, sourceIndex }))
          .filter(({ job }) => job.result_available)
      : [];
  const selectedIds = selection.map((item) => item.jobId);

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
                const checked = selection.some((item) => item.rowKey === rowKey);
                return (
                  <li key={rowKey}>
                    <label>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(event) => {
                          setSelection((current) =>
                            event.target.checked
                              ? [...current, { rowKey, jobId: job.job_id }]
                              : current.filter((item) => item.rowKey !== rowKey),
                          );
                        }}
                      />
                      <span><code>{job.job_id}</code> · <code>{job.run_id}</code></span>
                    </label>
                    <Link className="text-link" href={`/portfolio-records/${encodeURIComponent(job.job_id)}`}>
                      {t("inspect")}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </fieldset>
          <div className="comparison-selection__summary" aria-live="polite">
            <p>{t("selected", { count: selection.length })}</p>
            {selection.length > 0 ? (
              <ol aria-label={t("selectionOrder")}>
                {selection.map((item, index) => (
                  <li key={`${item.rowKey}-${index}`}><code>{item.jobId}</code></li>
                ))}
              </ol>
            ) : null}
            {selection.length >= 2 ? (
              <Link className="primary-link" href={comparisonHref(selectedIds)}>
                {t("compare")}
              </Link>
            ) : (
              <span className="disabled-action" aria-disabled="true">{t("chooseTwo")}</span>
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
          onRetry={retry}
          retryLabel={t("retry")}
        />
      ) : state.data.manifests.length === 0 ? (
        <div className="dashboard-state dashboard-state--empty"><p>{t("empty")}</p></div>
      ) : (
        <ol className="dashboard-source-list" aria-label={t("ariaLabel")}>
          {state.data.manifests.slice(0, DASHBOARD_SOURCE_LIMIT).map((manifest, index) => (
            <li key={`${manifest.manifest_type}-${manifest.artifact_key}-${index}`}>
              <div>
                <strong>{manifest.label ?? manifest.manifest_id}</strong>
                <code>{manifest.manifest_type} / {manifest.artifact_key}</code>
                <span>{t("references", { count: manifest.reference_count })}</span>
              </div>
              <Link className="text-link" href={`/evidence-manifests/${encodeURIComponent(manifest.manifest_type)}/${encodeURIComponent(manifest.artifact_key)}`}>
                {t("inspect")}
              </Link>
            </li>
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
          <Link href="/lifecycle-review">
            <span>{t("demo.lifecycle", { step: comparisonStep + 1 })}</span>
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
        {sources.map((source) => (
          <li key={source.endpoint}>
            <div>
              <strong>{source.label}</strong>
              <code>{source.endpoint}</code>
              {source.state.status === "error" ? (
                <>
                  <span>{common("errorCode", { code: source.state.code })}</span>
                  {source.state.requestId ? <span>{common("requestId", { requestId: source.state.requestId })}</span> : null}
                </>
              ) : source.state.status === "success" && source.state.requestId ? (
                <span>{common("requestId", { requestId: source.state.requestId })}</span>
              ) : null}
            </div>
            <button className="quiet-button" type="button" onClick={source.retry} disabled={source.state.status === "loading"}>
              {source.state.status === "loading" ? t("loading") : t("refresh", { source: source.label })}
            </button>
          </li>
        ))}
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
  const health = useApiResource(healthRequest);
  const research = useApiResource(researchRequest);
  const evidence = useApiResource(evidenceRequest);
  const jobs = useApiResource(jobsRequest);
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
          retryHealth={health.retry}
          retryEnvironment={environment.retry}
          retryResearch={research.retry}
          retryEvidence={evidence.retry}
          retryJobs={jobs.retry}
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
