"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useRef, useState } from "react";

import { ErrorState, LoadingState, RequestId } from "@/components/data-states";
import {
  PortfolioReviewOutcomeValue,
  PortfolioReviewStatusValue,
} from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import { PortfolioReviewEvidence } from "@/components/portfolio-review-evidence";
import {
  ApiClientError,
  fetchPortfolioReviewDetail,
  submitPortfolioReviewDecision,
  type PortfolioReviewCommandResponse,
  type PortfolioReviewDecisionRequest,
  type PortfolioReviewDetailResponse,
} from "@/lib/api-client";
import {
  isTimezoneAwareTimestamp,
  portfolioReviewDecisionOutcomes,
} from "@/lib/portfolio-reviews";
import { useApiResource } from "@/lib/use-api-resource";

type StringRow = { key: number; value: string };
type FieldErrors = Record<string, string>;
type Failure = {
  code: string;
  message: string;
  requestId: string | null;
  httpStatus: number | null;
};

function failureFrom(error: unknown): Failure {
  if (error instanceof ApiClientError) {
    return {
      code: error.code,
      message: error.publicMessage,
      requestId: error.requestId,
      httpStatus: error.status > 0 ? error.status : null,
    };
  }
  return {
    code: "api_unavailable",
    message: "The local API is unavailable.",
    requestId: null,
    httpStatus: null,
  };
}

function DecisionStringEditor({
  title,
  item,
  prefix,
  rows,
  setRows,
  nextKey,
  errors,
}: {
  title: string;
  item: string;
  prefix: string;
  rows: StringRow[];
  setRows: (rows: StringRow[]) => void;
  nextKey: () => number;
  errors: FieldErrors;
}) {
  const common = useTranslations("portfolioReviews.common");
  return (
    <div className="repeatable-editor">
      <div className="repeatable-heading">
        <div><h3>{title}</h3><p>{common("orderedValues")}</p></div>
        <button className="secondary-button" type="button" onClick={() => setRows([...rows, { key: nextKey(), value: "" }])}>{common("add", { item })}</button>
      </div>
      {rows.length === 0 ? <p className="repeatable-empty">{common("none")}</p> : (
        <div className="repeatable-list">
          {rows.map((row, index) => {
            const name = `${prefix}-${index}`;
            return (
              <div className="repeatable-row repeatable-row--portfolio-string" key={row.key}>
                <span className="row-number">{common("itemNumber", { item, number: index + 1 })}</span>
                <label>
                  {common("value")}
                  <input
                    value={row.value}
                    aria-invalid={errors[name] ? true : undefined}
                    aria-describedby={errors[name] ? `${name}-error` : undefined}
                    onChange={(event) => setRows(rows.map((candidate) => candidate.key === row.key ? { ...candidate, value: event.target.value } : candidate))}
                  />
                  {errors[name] ? <span className="field-error" id={`${name}-error`}>{errors[name]}</span> : null}
                </label>
                <button className="remove-button" type="button" onClick={() => setRows(rows.filter((candidate) => candidate.key !== row.key))}>{common("remove", { item, number: index + 1 })}</button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function DecisionForm({
  reviewId,
  detail,
  onSuccess,
}: {
  reviewId: string;
  detail: PortfolioReviewDetailResponse;
  onSuccess: (result: {
    response: PortfolioReviewCommandResponse;
    requestId: string | null;
  }) => void;
}) {
  const t = useTranslations("portfolioReviews.decision");
  const fields = useTranslations("portfolioReviews.fields");
  const common = useTranslations("portfolioReviews.common");
  const validation = useTranslations("portfolioReviews.validation");
  const outcomes = useTranslations("portfolioReviews.outcomes");
  const keyRef = useRef(0);
  const pendingRef = useRef(false);
  const validationRef = useRef<HTMLDivElement>(null);
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [decisionId, setDecisionId] = useState("");
  const [outcome, setOutcome] = useState<PortfolioReviewDecisionRequest["outcome"] | "">("");
  const [rationale, setRationale] = useState("");
  const [reviewedBy, setReviewedBy] = useState("");
  const [reviewedTimestamp, setReviewedTimestamp] = useState("");
  const [notes, setNotes] = useState<StringRow[]>([]);
  const [warnings, setWarnings] = useState<StringRow[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  const nextKey = () => ++keyRef.current;

  function buildRequest(): PortfolioReviewDecisionRequest | null {
    const nextErrors: FieldErrors = {};
    const required = (name: string, value: string) => {
      if (value.trim().length === 0) nextErrors[name] = validation("required");
    };
    if (idempotencyKey.trim().length === 0) {
      nextErrors["decision-idempotency-key"] = validation("idempotency");
    }
    required("decision-id", decisionId);
    if (outcome === "") nextErrors["decision-outcome"] = validation("decisionOutcome");
    required("decision-rationale", rationale);
    required("decision-reviewed-by", reviewedBy);
    if (!isTimezoneAwareTimestamp(reviewedTimestamp)) {
      nextErrors["decision-reviewed-timestamp"] = validation("timestamp");
    }
    notes.forEach((row, index) => {
      if (row.value.trim().length === 0) {
        nextErrors[`decision-note-${index}`] = validation("required");
      }
    });
    warnings.forEach((row, index) => {
      if (row.value.trim().length === 0) {
        nextErrors[`decision-warning-${index}`] = validation("required");
      }
    });
    if (!confirmed) {
      nextErrors["decision-confirmation"] = validation("decisionConfirmation");
    }
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0 || outcome === "") {
      queueMicrotask(() => validationRef.current?.focus());
      return null;
    }
    return {
      decision_id: decisionId,
      outcome,
      rationale,
      reviewed_by: reviewedBy,
      reviewed_timestamp: reviewedTimestamp,
      notes: notes.map((row) => row.value),
      warnings: warnings.map((row) => row.value),
    };
  }

  return (
    <form
      className="paper-job-form portfolio-decision-form"
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        if (pendingRef.current) return;
        const request = buildRequest();
        if (request === null) {
          setFailure(null);
          return;
        }
        pendingRef.current = true;
        setPending(true);
        setFailure(null);
        void submitPortfolioReviewDecision(reviewId, request, idempotencyKey)
          .then((result) => onSuccess({ response: result.data, requestId: result.requestId }))
          .catch((error: unknown) => setFailure(failureFrom(error)))
          .finally(() => {
            pendingRef.current = false;
            setPending(false);
          });
      }}
    >
      <div className="section-heading">
        <div><p className="eyebrow">{t("eyebrow")}</p><h2>{t("title")}</h2></div>
        <p>{t("description")}</p>
      </div>
      {Object.keys(errors).length > 0 ? (
        <div className="form-alert" role="alert" tabIndex={-1} ref={validationRef}>
          <strong>{t("attentionTitle")}</strong>
          <span>{t("attentionDescription")}</span>
        </div>
      ) : null}
      {failure ? (
        <>
          <ErrorState
            className="mutation-notice mutation-notice--error"
            title={t("attentionTitle")}
            code={failure.code}
            message={failure.message}
            requestId={failure.requestId}
            httpStatus={failure.httpStatus}
            operation="portfolio_review.decision"
            entityLabel={fields("reviewId")}
            entityId={detail.record.review_id}
          />
          <p className="neutral-note">{t("conflictGuidance")}</p>
        </>
      ) : null}
      <fieldset className="form-section">
        <legend>{t("title")}</legend>
        <div className="form-grid">
          {([
            ["decision-idempotency-key", fields("idempotencyKey"), idempotencyKey, setIdempotencyKey],
            ["decision-id", fields("decisionId"), decisionId, setDecisionId],
            ["decision-reviewed-by", fields("reviewedBy"), reviewedBy, setReviewedBy],
            ["decision-reviewed-timestamp", fields("reviewedTimestamp"), reviewedTimestamp, setReviewedTimestamp],
          ] as const).map(([name, label, value, setter]) => (
            <label key={name}>
              {label} <span className="required-label">{common("required")}</span>
              <input value={value} onChange={(event) => setter(event.target.value)} aria-invalid={errors[name] ? true : undefined} aria-describedby={errors[name] ? `${name}-error` : undefined} />
              {name.endsWith("timestamp") ? <span className="field-guidance">{common("timestampGuidance")}</span> : null}
              {errors[name] ? <span className="field-error" id={`${name}-error`}>{errors[name]}</span> : null}
            </label>
          ))}
          <label>
            {fields("outcome")} <span className="required-label">{common("required")}</span>
            <select value={outcome} onChange={(event) => setOutcome(event.target.value as PortfolioReviewDecisionRequest["outcome"] | "")} aria-invalid={errors["decision-outcome"] ? true : undefined} aria-describedby={errors["decision-outcome"] ? "decision-outcome-error" : undefined}>
              <option value="">{fields("selectExplicitly")}</option>
              {portfolioReviewDecisionOutcomes.map((value) => <option key={value} value={value}>{outcomes(value)} ({value})</option>)}
            </select>
            {errors["decision-outcome"] ? <span className="field-error" id="decision-outcome-error">{errors["decision-outcome"]}</span> : null}
          </label>
          <label className="form-grid__wide">
            {fields("rationale")} <span className="required-label">{common("required")}</span>
            <textarea value={rationale} onChange={(event) => setRationale(event.target.value)} aria-invalid={errors["decision-rationale"] ? true : undefined} aria-describedby={errors["decision-rationale"] ? "decision-rationale-error" : undefined} />
            {errors["decision-rationale"] ? <span className="field-error" id="decision-rationale-error">{errors["decision-rationale"]}</span> : null}
          </label>
        </div>
        <DecisionStringEditor title={common("notes")} item={common("notes")} prefix="decision-note" rows={notes} setRows={setNotes} nextKey={nextKey} errors={errors} />
        <DecisionStringEditor title={common("warnings")} item={common("warnings")} prefix="decision-warning" rows={warnings} setRows={setWarnings} nextKey={nextKey} errors={errors} />
      </fieldset>
      <fieldset className="form-section confirmation-panel">
        <legend>{t("eyebrow")}</legend>
        <label className="portfolio-confirmation">
          <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} aria-invalid={errors["decision-confirmation"] ? true : undefined} aria-describedby={errors["decision-confirmation"] ? "decision-confirmation-error" : undefined} />
          <span>{t("confirmation")}</span>
        </label>
        {errors["decision-confirmation"] ? <span className="field-error" id="decision-confirmation-error">{errors["decision-confirmation"]}</span> : null}
      </fieldset>
      <div className="submission-actions">
        <button className="primary-button" type="submit" disabled={pending}>{pending ? t("submitting") : t("submit")}</button>
        <p>{common("governanceBoundary")}</p>
      </div>
    </form>
  );
}

function ImmutableDecision({ detail }: { detail: PortfolioReviewDetailResponse }) {
  const t = useTranslations("portfolioReviews.detail");
  const decisionCopy = useTranslations("portfolioReviews.decision");
  const fields = useTranslations("portfolioReviews.fields");
  const common = useTranslations("portfolioReviews.common");
  const decision = detail.decision;
  if (decision === null) return <p>{t("noDecision")}</p>;
  return (
    <div className="evidence-card immutable-decision">
      <div className="evidence-card__heading">
        <h3>{t("immutableDecision")}</h3>
        <PortfolioReviewOutcomeValue value={decision.outcome} />
      </div>
      <p>{decisionCopy("settled")}</p>
      <dl className="definition-grid definition-grid--wide">
        <div><dt>{fields("decisionId")}</dt><dd><code className="raw-value">{decision.decision_id}</code></dd></div>
        <div><dt>{fields("outcome")}</dt><dd><code className="raw-value">{decision.outcome}</code></dd></div>
        <div><dt>{fields("rationale")}</dt><dd>{decision.rationale}</dd></div>
        <div><dt>{fields("reviewedBy")}</dt><dd><code className="raw-value">{decision.reviewed_by}</code></dd></div>
        <div><dt>{fields("reviewedTimestamp")}</dt><dd><code className="raw-value">{decision.reviewed_timestamp}</code></dd></div>
        <div><dt>{t("decisionScope")}</dt><dd><code className="raw-value">{decision.decision_scope}</code></dd></div>
        <div><dt>{common("notes")}</dt><dd><ol className="raw-value-list">{decision.notes.map((note, index) => <li key={`${index}-${note}`}>{note}</li>)}</ol></dd></div>
        <div><dt>{common("warnings")}</dt><dd><ol className="raw-value-list">{decision.warnings.map((warning, index) => <li key={`${index}-${warning}`}>{warning}</li>)}</ol></dd></div>
        <div><dt>{common("decisionDigest")}</dt><dd><code className="raw-value">{decision.decision_digest}</code></dd></div>
      </dl>
    </div>
  );
}

function RawAudit({ detail }: { detail: PortfolioReviewDetailResponse }) {
  const t = useTranslations("portfolioReviews.detail");
  const common = useTranslations("portfolioReviews.common");
  const record = detail.record;
  const analysis = detail.analysis;
  return (
    <section className="content-panel portfolio-evidence-section" id="raw-audit" aria-labelledby="raw-audit-title">
      <div className="section-heading"><div><h2 id="raw-audit-title">{t("rawAudit")}</h2></div><p>{common("historicalBoundary")}</p></div>
      <dl className="definition-grid definition-grid--wide raw-audit-grid">
        {([
          ["record_schema_version", record.record_schema_version],
          ["source_schema_version", record.source_schema_version],
          ["analysis_schema_version", record.analysis_schema_version],
          ["decision_schema_version", record.decision_schema_version],
          ["source_digest", record.source_digest],
          ["baseline_scenario_digest", record.baseline_scenario_digest],
          ["proposed_scenario_digest", record.proposed_scenario_digest],
          ["analysis_digest", record.analysis_digest],
          ["decision_digest", record.decision_digest],
          ["created_timestamp", record.created_timestamp],
          ["updated_timestamp", record.updated_timestamp],
          ["reviewed_timestamp", record.reviewed_timestamp],
          ["analysis_evidence_scope", analysis.analysis_evidence_scope],
          ["analysis_created_timestamp", analysis.created_timestamp],
        ] as const).map(([label, value]) => (
          <div key={label}><dt>{label}</dt><dd>{value === null ? common("notAvailable") : <code className="raw-value">{String(value)}</code>}</dd></div>
        ))}
      </dl>
    </section>
  );
}

const sectionLinks = [
  "source",
  "observations",
  "scenarios",
  "concentration",
  "exposure",
  "overlap",
  "correlation",
  "behavior",
  "contribution",
  "impact",
  "limitations",
  "decision",
  "rawAudit",
] as const;

export function PortfolioReviewDetailView({ reviewId }: { reviewId: string }) {
  const t = useTranslations("portfolioReviews.detail");
  const common = useTranslations("portfolioReviews.common");
  const decisionCopy = useTranslations("portfolioReviews.decision");
  const fields = useTranslations("portfolioReviews.fields");
  const [detail, setDetail] = useState<PortfolioReviewDetailResponse | null>(null);
  const [decisionResult, setDecisionResult] = useState<{
    response: PortfolioReviewCommandResponse;
    requestId: string | null;
  } | null>(null);
  const successRef = useRef<HTMLDivElement>(null);
  const request = useCallback(async () => {
    const result = await fetchPortfolioReviewDetail(reviewId);
    setDetail(result.data);
    setDecisionResult(null);
    return result;
  }, [reviewId]);
  const { state, retry } = useApiResource(request);

  const refreshPending = state.status === "loading" && detail !== null;
  if (detail === null && state.status === "loading") {
    return (
      <div className="business-workspace">
        <LoadingState message={t("loading")} />
      </div>
    );
  }
  if (detail === null && state.status === "error") {
    return (
      <div className="business-workspace">
        <ErrorState
          code={state.code}
          title={t("unavailableTitle")}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="portfolio_review.detail"
          entityLabel={fields("reviewId")}
          entityId={reviewId}
          onRetry={state.code === "portfolio_review_not_found" ? undefined : retry}
          backHref="/portfolio-reviews"
          backLabel={t("back")}
        />
      </div>
    );
  }
  if (detail === null) return null;

  return (
    <div className="business-workspace portfolio-review-detail">
      <div className="back-links">
        <Link className="text-link" href="/portfolio-reviews">{t("back")}</Link>
      </div>
      <header className="page-heading page-heading--with-action">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p className="identity-line">{detail.record.review_id}</p>
          <p>{t("description")}</p>
        </div>
        <div className="record-card__actions">
          <button className="secondary-button" type="button" onClick={retry}>{t("refresh")}</button>
          <Link className="primary-link" href="/portfolio-reviews/new">{t("createAnother")}</Link>
        </div>
      </header>

      {refreshPending ? <p className="neutral-note" role="status">{t("refreshPending")}</p> : null}
      {state.status === "error" ? (
        <ErrorState
          title={t("unavailableTitle")}
          code={state.code}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="portfolio_review.detail"
          entityLabel={fields("reviewId")}
          entityId={reviewId}
          onRetry={retry}
        />
      ) : null}
      {decisionResult ? (
        <div className="mutation-notice mutation-notice--success" role="status" tabIndex={-1} ref={successRef}>
          <h2>{decisionResult.response.outcome === "created" ? decisionCopy("createdTitle") : decisionCopy("replayedTitle")}</h2>
          <p>{decisionResult.response.outcome === "created" ? decisionCopy("createdDescription") : decisionCopy("replayedDescription")}</p>
          <code className="raw-value">{decisionResult.response.outcome}</code>
          <RequestId value={decisionResult.requestId} />
        </div>
      ) : null}

      <section className="content-panel status-audit" aria-labelledby="status-audit-title">
        <div className="section-heading"><div><h2 id="status-audit-title">{t("statusAudit")}</h2></div><p>{common("governanceBoundary")}</p></div>
        <dl className="definition-grid definition-grid--wide">
          <div><dt>{fields("reviewId")}</dt><dd><code className="raw-value">{detail.record.review_id}</code></dd></div>
          <div><dt>{t("status")}</dt><dd><PortfolioReviewStatusValue value={detail.record.status} /></dd></div>
          <div><dt>{fields("sourceId")}</dt><dd><code className="raw-value">{detail.record.source_id}</code></dd></div>
          <div><dt>{fields("proposedComponent")}</dt><dd><code className="raw-value">{detail.record.proposed_component_id}</code></dd></div>
          <div><dt>{t("createdBy")}</dt><dd><code className="raw-value">{detail.record.created_by}</code></dd></div>
          <div><dt>{fields("createdTimestamp")}</dt><dd><LocalizedTimestamp value={detail.record.created_timestamp} /></dd></div>
          <div><dt>{t("updated")}</dt><dd><LocalizedTimestamp value={detail.record.updated_timestamp} /></dd></div>
          <div><dt>{t("version")}</dt><dd><code className="raw-value">{detail.record.version}</code></dd></div>
        </dl>
      </section>

      <nav className="section-navigation portfolio-section-navigation" aria-label={t("navigationAria")}>
        {sectionLinks.map((key) => (
          <a key={key} href={`#${key === "rawAudit" ? "raw-audit" : key}`}>{t(key)}</a>
        ))}
      </nav>

      <PortfolioReviewEvidence detail={detail} />

      <section className="content-panel portfolio-evidence-section" id="decision" aria-labelledby="decision-title">
        <div className="section-heading"><div><h2 id="decision-title">{t("decision")}</h2></div><p>{common("governanceBoundary")}</p></div>
        {detail.record.status === "awaiting_decision" ? (
          <DecisionForm
            key={detail.record.review_id}
            reviewId={reviewId}
            detail={detail}
            onSuccess={(nextResult) => {
              setDetail(nextResult.response.review);
              setDecisionResult(nextResult);
              queueMicrotask(() => successRef.current?.focus());
            }}
          />
        ) : (
          <ImmutableDecision detail={detail} />
        )}
      </section>

      <RawAudit detail={detail} />
    </div>
  );
}
