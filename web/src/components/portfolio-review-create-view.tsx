"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useRef, useState } from "react";

import { ErrorState, RequestId } from "@/components/data-states";
import {
  ApiClientError,
  createPortfolioReview,
  type PortfolioReviewCommandResponse,
  type PortfolioReviewCreateRequest,
} from "@/lib/api-client";
import {
  acceptedScenarioWeightTotal,
  isTimezoneAwareTimestamp,
  parsePortfolioReviewDecimal,
  portfolioReviewEvidenceReferenceTypes,
  portfolioReviewResearchReferenceTypes,
  scenarioWeightTotal,
  type PortfolioReviewEvidenceReferenceType,
} from "@/lib/portfolio-reviews";

type FieldErrors = Record<string, string>;
type StringRow = { key: number; value: string };
type EvidenceRow = {
  key: number;
  referenceType: PortfolioReviewEvidenceReferenceType | "";
  referenceId: string;
  label: string;
  description: string;
};
type ComponentRow = {
  key: number;
  componentId: string;
  strategyId: string;
  label: string;
  description: string;
  evidence: EvidenceRow[];
  symbols: StringRow[];
  baselineWeight: string;
  proposedWeight: string;
};
type ObservationRow = {
  key: number;
  timestamp: string;
  returns: Record<number, string>;
};
type ScenarioDraft = {
  scenarioId: string;
  rationale: string;
  assumptions: StringRow[];
  warnings: StringRow[];
};
type Failure = {
  code: string;
  message: string;
  requestId: string | null;
  httpStatus: number | null;
};

const initialComponents: ComponentRow[] = [
  {
    key: -1,
    componentId: "",
    strategyId: "",
    label: "",
    description: "",
    evidence: [{
      key: -11,
      referenceType: "",
      referenceId: "",
      label: "",
      description: "",
    }],
    symbols: [],
    baselineWeight: "",
    proposedWeight: "",
  },
  {
    key: -2,
    componentId: "",
    strategyId: "",
    label: "",
    description: "",
    evidence: [{
      key: -12,
      referenceType: "",
      referenceId: "",
      label: "",
      description: "",
    }],
    symbols: [],
    baselineWeight: "",
    proposedWeight: "",
  },
];

const initialObservations: ObservationRow[] = [-21, -22, -23].map((key) => ({
  key,
  timestamp: "",
  returns: { [-1]: "", [-2]: "" },
}));

function blankScenario(): ScenarioDraft {
  return { scenarioId: "", rationale: "", assumptions: [], warnings: [] };
}

function FieldError({ id, message }: { id: string; message?: string }) {
  return message ? <span className="field-error" id={id}>{message}</span> : null;
}

function fieldA11y(errors: FieldErrors, name: string) {
  return {
    "aria-invalid": errors[name] ? true : undefined,
    "aria-describedby": errors[name] ? `${name}-error` : undefined,
  };
}

function StringListEditor({
  title,
  item,
  idPrefix,
  rows,
  setRows,
  nextKey,
  errors,
}: {
  title: string;
  item: string;
  idPrefix: string;
  rows: StringRow[];
  setRows: (rows: StringRow[]) => void;
  nextKey: () => number;
  errors: FieldErrors;
}) {
  const t = useTranslations("portfolioReviews.common");
  return (
    <div className="repeatable-editor">
      <div className="repeatable-heading">
        <div>
          <h3>{title}</h3>
          <p>{t("orderedValues")}</p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => setRows([...rows, { key: nextKey(), value: "" }])}
        >
          {t("add", { item })}
        </button>
      </div>
      {rows.length === 0 ? <p className="repeatable-empty">{t("none")}</p> : (
        <div className="repeatable-list">
          {rows.map((row, index) => {
            const name = `${idPrefix}-${index}`;
            return (
              <div className="repeatable-row repeatable-row--portfolio-string" key={row.key}>
                <span className="row-number">{t("itemNumber", { item, number: index + 1 })}</span>
                <label htmlFor={name}>
                  {t("value")}
                  <input
                    id={name}
                    value={row.value}
                    onChange={(event) =>
                      setRows(rows.map((candidate) =>
                        candidate.key === row.key
                          ? { ...candidate, value: event.target.value }
                          : candidate,
                      ))
                    }
                    {...fieldA11y(errors, name)}
                  />
                  <FieldError id={`${name}-error`} message={errors[name]} />
                </label>
                <button
                  className="remove-button"
                  type="button"
                  onClick={() =>
                    setRows(rows.filter((candidate) => candidate.key !== row.key))
                  }
                >
                  {t("remove", { item, number: index + 1 })}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

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

export function PortfolioReviewCreateView() {
  const t = useTranslations("portfolioReviews.create");
  const fields = useTranslations("portfolioReviews.fields");
  const validation = useTranslations("portfolioReviews.validation");
  const common = useTranslations("portfolioReviews.common");
  const keyRef = useRef(0);
  const pendingRef = useRef(false);
  const validationRef = useRef<HTMLDivElement>(null);
  const successRef = useRef<HTMLDivElement>(null);
  const nextKey = () => ++keyRef.current;

  const [reviewId, setReviewId] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [sourceCreatedBy, setSourceCreatedBy] = useState("");
  const [sourceCreatedTimestamp, setSourceCreatedTimestamp] = useState("");
  const [evaluationFrequency, setEvaluationFrequency] = useState("");
  const [periodsPerYear, setPeriodsPerYear] = useState("");
  const [sourceAssumptions, setSourceAssumptions] = useState<StringRow[]>([]);
  const [sourceWarnings, setSourceWarnings] = useState<StringRow[]>([]);
  const [sourceMissing, setSourceMissing] = useState<StringRow[]>([]);
  const [components, setComponents] = useState<ComponentRow[]>(initialComponents);
  const [observations, setObservations] =
    useState<ObservationRow[]>(initialObservations);
  const [baseline, setBaseline] = useState<ScenarioDraft>(blankScenario);
  const [proposed, setProposed] = useState<ScenarioDraft>(blankScenario);
  const [proposedComponentKey, setProposedComponentKey] = useState("");
  const [analysisCreatedBy, setAnalysisCreatedBy] = useState("");
  const [analysisCreatedTimestamp, setAnalysisCreatedTimestamp] = useState("");
  const [analysisAssumptions, setAnalysisAssumptions] = useState<StringRow[]>([]);
  const [analysisWarnings, setAnalysisWarnings] = useState<StringRow[]>([]);
  const [analysisMissing, setAnalysisMissing] = useState<StringRow[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [pending, setPending] = useState(false);
  const [serverError, setServerError] = useState<Failure | null>(null);
  const [result, setResult] = useState<{
    response: PortfolioReviewCommandResponse;
    requestId: string | null;
  } | null>(null);

  function addComponent() {
    if (components.length >= 12) return;
    const key = nextKey();
    setComponents([...components, {
      key,
      componentId: "",
      strategyId: "",
      label: "",
      description: "",
      evidence: [],
      symbols: [],
      baselineWeight: "",
      proposedWeight: "",
    }]);
    setObservations(observations.map((row) => ({
      ...row,
      returns: { ...row.returns, [key]: "" },
    })));
  }

  function removeComponent(key: number) {
    if (components.length <= 2) return;
    setComponents(components.filter((component) => component.key !== key));
    setObservations(observations.map((row) => {
      const nextReturns = { ...row.returns };
      delete nextReturns[key];
      return { ...row, returns: nextReturns };
    }));
    const removed = components.find((component) => component.key === key);
    if (removed?.componentId === proposedComponentKey) {
      setProposedComponentKey("");
    }
  }

  function validateStringRows(
    rows: StringRow[],
    prefix: string,
    nextErrors: FieldErrors,
  ) {
    rows.forEach((row, index) => {
      if (row.value.trim().length === 0) {
        nextErrors[`${prefix}-${index}`] = validation("required");
      }
    });
  }

  function buildRequest(): PortfolioReviewCreateRequest | null {
    const nextErrors: FieldErrors = {};
    const numeric = new Map<string, number>();
    const required = (name: string, value: string) => {
      if (value.trim().length === 0) {
        nextErrors[name] = validation("required");
      }
    };
    const timestamp = (name: string, value: string) => {
      if (!isTimezoneAwareTimestamp(value)) {
        nextErrors[name] = validation("timestamp");
      }
    };
    const decimal = (
      name: string,
      value: string,
      constraint: "finite" | "positive" | "non-negative" = "finite",
    ) => {
      const parsed = parsePortfolioReviewDecimal(value);
      if (parsed === null) {
        nextErrors[name] = validation("number");
      } else if (constraint === "positive" && parsed <= 0) {
        nextErrors[name] = validation("positive");
      } else if (constraint === "non-negative" && parsed < 0) {
        nextErrors[name] = validation("nonNegative");
      } else {
        numeric.set(name, parsed);
      }
    };

    required("review-id", reviewId);
    if (idempotencyKey.trim().length === 0) {
      nextErrors["idempotency-key"] = validation("idempotency");
    }
    required("source-id", sourceId);
    required("source-created-by", sourceCreatedBy);
    timestamp("source-created-timestamp", sourceCreatedTimestamp);
    required("evaluation-frequency", evaluationFrequency);
    if (periodsPerYear.trim().length > 0) {
      decimal("periods-per-year", periodsPerYear, "positive");
    }
    if (components.length < 2 || components.length > 12) {
      nextErrors.components = validation("componentCount");
    }
    const componentIds = new Set<string>();
    components.forEach((component, componentIndex) => {
      const prefix = `component-${componentIndex}`;
      required(`${prefix}-id`, component.componentId);
      required(`${prefix}-strategy`, component.strategyId);
      if (
        component.componentId.trim().length > 0 &&
        componentIds.has(component.componentId)
      ) {
        nextErrors[`${prefix}-id`] = validation("duplicateComponent");
      }
      componentIds.add(component.componentId);
      if (component.evidence.length === 0) {
        nextErrors[`${prefix}-evidence`] = validation("evidenceRequired");
      }
      const evidenceIds = new Set<string>();
      let hasResearchEvidence = false;
      component.evidence.forEach((evidence, evidenceIndex) => {
        const evidencePrefix = `${prefix}-evidence-${evidenceIndex}`;
        if (evidence.referenceType === "") {
          nextErrors[`${evidencePrefix}-type`] = validation("required");
        } else if (portfolioReviewResearchReferenceTypes.has(evidence.referenceType)) {
          hasResearchEvidence = true;
        }
        required(`${evidencePrefix}-id`, evidence.referenceId);
        const identity = `${evidence.referenceType}\u0000${evidence.referenceId}`;
        if (
          evidence.referenceType !== "" &&
          evidence.referenceId.trim().length > 0 &&
          evidenceIds.has(identity)
        ) {
          nextErrors[`${evidencePrefix}-id`] = validation("duplicateEvidence");
        }
        evidenceIds.add(identity);
      });
      if (component.evidence.length > 0 && !hasResearchEvidence) {
        nextErrors[`${prefix}-evidence`] = validation("researchEvidence");
      }
      component.symbols.forEach((symbol, symbolIndex) => {
        if (symbol.value.trim().length === 0) {
          nextErrors[`${prefix}-symbol-${symbolIndex}`] = validation("symbol");
        }
      });
      decimal(`${prefix}-baseline-weight`, component.baselineWeight, "non-negative");
      decimal(`${prefix}-proposed-weight`, component.proposedWeight, "non-negative");
    });

    if (observations.length < 3) {
      nextErrors.observations = validation("observationCount");
    }
    const observationTimestamps = new Set<string>();
    let priorTimestamp = Number.NEGATIVE_INFINITY;
    observations.forEach((observation, observationIndex) => {
      const prefix = `observation-${observationIndex}`;
      timestamp(`${prefix}-timestamp`, observation.timestamp);
      if (
        observation.timestamp.length > 0 &&
        observationTimestamps.has(observation.timestamp)
      ) {
        nextErrors[`${prefix}-timestamp`] = validation("duplicateTimestamp");
      }
      observationTimestamps.add(observation.timestamp);
      const parsedTimestamp = Date.parse(observation.timestamp);
      if (
        Number.isFinite(parsedTimestamp) &&
        priorTimestamp !== Number.NEGATIVE_INFINITY &&
        parsedTimestamp <= priorTimestamp
      ) {
        nextErrors[`${prefix}-timestamp`] = validation("timestampOrder");
      }
      if (Number.isFinite(parsedTimestamp)) priorTimestamp = parsedTimestamp;
      components.forEach((component, componentIndex) => {
        decimal(
          `${prefix}-return-${componentIndex}`,
          observation.returns[component.key] ?? "",
        );
      });
    });

    required("baseline-scenario-id", baseline.scenarioId);
    required("baseline-rationale", baseline.rationale);
    required("proposed-scenario-id", proposed.scenarioId);
    required("proposed-rationale", proposed.rationale);
    if (
      proposedComponentKey.length === 0 ||
      !components.some((component) => component.componentId === proposedComponentKey)
    ) {
      nextErrors["proposed-component"] = validation("proposedComponent");
    }
    required("analysis-created-by", analysisCreatedBy);
    timestamp("analysis-created-timestamp", analysisCreatedTimestamp);
    validateStringRows(sourceAssumptions, "source-assumption", nextErrors);
    validateStringRows(sourceWarnings, "source-warning", nextErrors);
    validateStringRows(sourceMissing, "source-missing", nextErrors);
    validateStringRows(baseline.assumptions, "baseline-assumption", nextErrors);
    validateStringRows(baseline.warnings, "baseline-warning", nextErrors);
    validateStringRows(proposed.assumptions, "proposed-assumption", nextErrors);
    validateStringRows(proposed.warnings, "proposed-warning", nextErrors);
    validateStringRows(analysisAssumptions, "analysis-assumption", nextErrors);
    validateStringRows(analysisWarnings, "analysis-warning", nextErrors);
    validateStringRows(analysisMissing, "analysis-missing", nextErrors);

    const baselineTotal = scenarioWeightTotal(
      components.map((component) => component.baselineWeight),
    );
    const proposedTotal = scenarioWeightTotal(
      components.map((component) => component.proposedWeight),
    );
    if (baselineTotal !== null && !acceptedScenarioWeightTotal(baselineTotal)) {
      nextErrors["baseline-total"] = validation("weightTotal");
    }
    if (proposedTotal !== null && !acceptedScenarioWeightTotal(proposedTotal)) {
      nextErrors["proposed-total"] = validation("weightTotal");
    }
    const baselineNumbers = components.map((component, index) =>
      numeric.get(`component-${index}-baseline-weight`),
    );
    const proposedNumbers = components.map((component, index) =>
      numeric.get(`component-${index}-proposed-weight`),
    );
    if (baselineNumbers.every((value) => value === 0)) {
      nextErrors["baseline-total"] = validation("scenarioPositive");
    }
    if (proposedNumbers.every((value) => value === 0)) {
      nextErrors["proposed-total"] = validation("scenarioPositive");
    }
    if (
      baselineNumbers.every((value, index) =>
        value !== undefined && value === proposedNumbers[index],
      )
    ) {
      nextErrors["proposed-total"] = validation("scenariosDiffer");
    }
    if (!confirmed) {
      nextErrors.confirmation = validation("confirmation");
    }
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      queueMicrotask(() => validationRef.current?.focus());
      return null;
    }

    const numberValue = (name: string): number => {
      const value = numeric.get(name);
      if (value === undefined) {
        throw new Error(`Missing validated numeric field ${name}`);
      }
      return value;
    };
    const selectedComponent = components.find(
      (component) => component.componentId === proposedComponentKey,
    );
    if (selectedComponent === undefined) {
      throw new Error("Missing validated proposed component");
    }
    const weights = (kind: "baseline" | "proposed") =>
      Object.fromEntries(components.map((component, index) => [
        component.componentId,
        numberValue(`component-${index}-${kind}-weight`),
      ]));
    const stringValues = (rows: StringRow[]) => rows.map((row) => row.value);

    return {
      review_id: reviewId,
      source: {
        source_id: sourceId,
        components: components.map((component) => ({
          component_id: component.componentId,
          strategy_id: component.strategyId,
          evidence_references: component.evidence.map((evidence) => ({
            reference_type: evidence.referenceType,
            reference_id: evidence.referenceId,
            label: evidence.label.trim().length === 0 ? null : evidence.label,
            description:
              evidence.description.trim().length === 0
                ? null
                : evidence.description,
          })),
          symbols:
            component.symbols.length === 0
              ? null
              : stringValues(component.symbols),
          label: component.label.trim().length === 0 ? null : component.label,
          description:
            component.description.trim().length === 0
              ? null
              : component.description,
        })),
        return_observations: observations.map((observation, observationIndex) => ({
          timestamp: observation.timestamp,
          component_returns: components.map((_, componentIndex) =>
            numberValue(`observation-${observationIndex}-return-${componentIndex}`),
          ),
        })),
        evaluation_frequency: evaluationFrequency,
        periods_per_year:
          periodsPerYear.trim().length === 0
            ? null
            : numberValue("periods-per-year"),
        created_by: sourceCreatedBy,
        created_timestamp: sourceCreatedTimestamp,
        assumptions: stringValues(sourceAssumptions),
        warnings: stringValues(sourceWarnings),
        missing_evidence: stringValues(sourceMissing),
      },
      baseline_scenario: {
        scenario_id: baseline.scenarioId,
        weights: weights("baseline"),
        rationale: baseline.rationale,
        assumptions: stringValues(baseline.assumptions),
        warnings: stringValues(baseline.warnings),
      },
      proposed_scenario: {
        scenario_id: proposed.scenarioId,
        weights: weights("proposed"),
        rationale: proposed.rationale,
        assumptions: stringValues(proposed.assumptions),
        warnings: stringValues(proposed.warnings),
        proposed_component_id: selectedComponent.componentId,
      },
      analysis: {
        created_by: analysisCreatedBy,
        created_timestamp: analysisCreatedTimestamp,
        assumptions: stringValues(analysisAssumptions),
        warnings: stringValues(analysisWarnings),
        missing_evidence: stringValues(analysisMissing),
      },
    };
  }

  const baselineTotal = scenarioWeightTotal(
    components.map((component) => component.baselineWeight),
  );
  const proposedTotal = scenarioWeightTotal(
    components.map((component) => component.proposedWeight),
  );

  return (
    <div className="business-workspace">
      <div className="back-links">
        <Link className="text-link" href="/portfolio-reviews">{t("back")}</Link>
      </div>
      <header className="page-heading page-heading--detail">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
      </header>

      <div className="boundary-card portfolio-review-boundary">
        <p>{common("historicalBoundary")}</p>
        <p>{common("weightBoundary")}</p>
        <p>{common("governanceBoundary")}</p>
      </div>

      <form
        className="paper-job-form portfolio-review-form"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          if (pendingRef.current) return;
          const request = buildRequest();
          if (request === null) {
            setServerError(null);
            return;
          }
          pendingRef.current = true;
          setPending(true);
          setServerError(null);
          setResult(null);
          void createPortfolioReview(request, idempotencyKey)
            .then((response) => {
              setResult({ response: response.data, requestId: response.requestId });
              queueMicrotask(() => successRef.current?.focus());
            })
            .catch((error: unknown) => setServerError(failureFrom(error)))
            .finally(() => {
              pendingRef.current = false;
              setPending(false);
            });
        }}
      >
        {Object.keys(errors).length > 0 ? (
          <div className="form-alert" role="alert" tabIndex={-1} ref={validationRef}>
            <strong>{t("attentionTitle")}</strong>
            <span>{t("attentionDescription")}</span>
          </div>
        ) : null}
        {serverError ? (
          <ErrorState
            className="form-alert form-alert--server"
            title={t("attentionTitle")}
            code={serverError.code}
            message={serverError.message}
            requestId={serverError.requestId}
            httpStatus={serverError.httpStatus}
            operation="portfolio_review.create"
          />
        ) : null}
        {result ? (
          <div
            className="mutation-notice mutation-notice--success"
            role="status"
            tabIndex={-1}
            ref={successRef}
          >
            <h2>
              {result.response.outcome === "created"
                ? t("createdTitle")
                : t("replayedTitle")}
            </h2>
            <p>
              {result.response.outcome === "created"
                ? t("createdDescription")
                : t("replayedDescription")}
            </p>
            <code className="raw-value">{result.response.outcome}</code>
            <p>{t("noRedirect")}</p>
            <Link
              className="primary-link"
              href={`/portfolio-reviews/${encodeURIComponent(result.response.review.record.review_id)}`}
            >
              {t("inspect")}
            </Link>
            <RequestId value={result.requestId} />
          </div>
        ) : null}

        <fieldset className="form-section">
          <legend>{t("identityLegend")}</legend>
          <p className="form-section__description">{t("identityDescription")}</p>
          <div className="form-grid">
            <label>
              {fields("reviewId")} <span className="required-label">{common("required")}</span>
              <input id="review-id" value={reviewId} onChange={(event) => setReviewId(event.target.value)} {...fieldA11y(errors, "review-id")} />
              <FieldError id="review-id-error" message={errors["review-id"]} />
            </label>
            <label>
              {fields("idempotencyKey")} <span className="required-label">{common("required")}</span>
              <input id="idempotency-key" value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} {...fieldA11y(errors, "idempotency-key")} />
              <FieldError id="idempotency-key-error" message={errors["idempotency-key"]} />
            </label>
          </div>
        </fieldset>

        <fieldset className="form-section">
          <legend>{t("sourceLegend")}</legend>
          <p className="form-section__description">{t("sourceDescription")}</p>
          <div className="form-grid">
            {([
              ["source-id", fields("sourceId"), sourceId, setSourceId],
              ["source-created-by", fields("createdBy"), sourceCreatedBy, setSourceCreatedBy],
              ["source-created-timestamp", fields("createdTimestamp"), sourceCreatedTimestamp, setSourceCreatedTimestamp],
              ["evaluation-frequency", fields("evaluationFrequency"), evaluationFrequency, setEvaluationFrequency],
            ] as const).map(([name, label, value, setter]) => (
              <label key={name}>
                {label} <span className="required-label">{common("required")}</span>
                <input id={name} value={value} onChange={(event) => setter(event.target.value)} {...fieldA11y(errors, name)} />
                {name.endsWith("timestamp") ? <span className="field-guidance">{common("timestampGuidance")}</span> : null}
                <FieldError id={`${name}-error`} message={errors[name]} />
              </label>
            ))}
            <label>
              {fields("periodsPerYear")} <span className="optional-label">{common("optional")}</span>
              <input id="periods-per-year" inputMode="decimal" value={periodsPerYear} onChange={(event) => setPeriodsPerYear(event.target.value)} {...fieldA11y(errors, "periods-per-year")} />
              <FieldError id="periods-per-year-error" message={errors["periods-per-year"]} />
            </label>
          </div>
          <StringListEditor title={common("assumptions")} item={t("assumption")} idPrefix="source-assumption" rows={sourceAssumptions} setRows={setSourceAssumptions} nextKey={nextKey} errors={errors} />
          <StringListEditor title={common("warnings")} item={t("warning")} idPrefix="source-warning" rows={sourceWarnings} setRows={setSourceWarnings} nextKey={nextKey} errors={errors} />
          <StringListEditor title={common("missingEvidence")} item={t("missingEvidenceItem")} idPrefix="source-missing" rows={sourceMissing} setRows={setSourceMissing} nextKey={nextKey} errors={errors} />
        </fieldset>

        <fieldset className="form-section">
          <legend>{t("componentsLegend")}</legend>
          <p className="form-section__description">{t("componentsDescription")}</p>
          <button className="secondary-button" type="button" onClick={addComponent} disabled={components.length >= 12}>{t("addComponent")}</button>
          <FieldError id="components-error" message={errors.components} />
          <div className="portfolio-component-list">
            {components.map((component, componentIndex) => {
              const prefix = `component-${componentIndex}`;
              const update = (next: Partial<ComponentRow>) =>
                setComponents(components.map((candidate) =>
                  candidate.key === component.key ? { ...candidate, ...next } : candidate,
                ));
              return (
                <fieldset className="portfolio-component-editor" key={component.key}>
                  <legend>{common("itemNumber", { item: t("component"), number: componentIndex + 1 })}</legend>
                  <div className="form-grid">
                    {([
                      ["id", fields("componentId"), component.componentId, "componentId"],
                      ["strategy", fields("strategyId"), component.strategyId, "strategyId"],
                      ["label", fields("label"), component.label, "label"],
                      ["description", fields("description"), component.description, "description"],
                    ] as const).map(([suffix, label, value, field]) => {
                      const name = `${prefix}-${suffix}`;
                      const optional = field === "label" || field === "description";
                      return (
                        <label key={suffix}>
                          {label} <span className={optional ? "optional-label" : "required-label"}>{optional ? common("optional") : common("required")}</span>
                          <input value={value} onChange={(event) => update({ [field]: event.target.value })} {...fieldA11y(errors, name)} />
                          <FieldError id={`${name}-error`} message={errors[name]} />
                        </label>
                      );
                    })}
                  </div>
                  <div className="repeatable-heading">
                    <div><h3>{t("evidenceReference")}</h3><p>{common("orderedValues")}</p></div>
                    <button className="secondary-button" type="button" onClick={() => update({ evidence: [...component.evidence, { key: nextKey(), referenceType: "", referenceId: "", label: "", description: "" }] })}>{t("addEvidence")}</button>
                  </div>
                  <FieldError id={`${prefix}-evidence-error`} message={errors[`${prefix}-evidence`]} />
                  <div className="repeatable-list">
                    {component.evidence.map((evidence, evidenceIndex) => {
                      const evidencePrefix = `${prefix}-evidence-${evidenceIndex}`;
                      const updateEvidence = (next: Partial<EvidenceRow>) =>
                        update({ evidence: component.evidence.map((candidate) => candidate.key === evidence.key ? { ...candidate, ...next } : candidate) });
                      return (
                        <div className="repeatable-row portfolio-evidence-row" key={evidence.key}>
                          <span className="row-number">{common("itemNumber", { item: t("evidenceReference"), number: evidenceIndex + 1 })}</span>
                          <label>
                            {fields("referenceType")} <span className="required-label">{common("required")}</span>
                            <select value={evidence.referenceType} onChange={(event) => updateEvidence({ referenceType: event.target.value as PortfolioReviewEvidenceReferenceType | "" })} {...fieldA11y(errors, `${evidencePrefix}-type`)}>
                              <option value="">{fields("selectExplicitly")}</option>
                              {portfolioReviewEvidenceReferenceTypes.map((type) => <option key={type} value={type}>{type}</option>)}
                            </select>
                            <FieldError id={`${evidencePrefix}-type-error`} message={errors[`${evidencePrefix}-type`]} />
                          </label>
                          <label>
                            {fields("referenceId")} <span className="required-label">{common("required")}</span>
                            <input value={evidence.referenceId} onChange={(event) => updateEvidence({ referenceId: event.target.value })} {...fieldA11y(errors, `${evidencePrefix}-id`)} />
                            <FieldError id={`${evidencePrefix}-id-error`} message={errors[`${evidencePrefix}-id`]} />
                          </label>
                          <label>{fields("label")} <span className="optional-label">{common("optional")}</span><input value={evidence.label} onChange={(event) => updateEvidence({ label: event.target.value })} /></label>
                          <label>{fields("description")} <span className="optional-label">{common("optional")}</span><input value={evidence.description} onChange={(event) => updateEvidence({ description: event.target.value })} /></label>
                          <button className="remove-button" type="button" onClick={() => update({ evidence: component.evidence.filter((candidate) => candidate.key !== evidence.key) })}>{common("remove", { item: t("evidenceReference"), number: evidenceIndex + 1 })}</button>
                        </div>
                      );
                    })}
                  </div>
                  <StringListEditor title={fields("label") + " / " + t("symbol")} item={t("symbol")} idPrefix={`${prefix}-symbol`} rows={component.symbols} setRows={(symbols) => update({ symbols })} nextKey={nextKey} errors={errors} />
                  <button className="remove-button" type="button" disabled={components.length <= 2} onClick={() => removeComponent(component.key)}>{t("removeComponent", { number: componentIndex + 1 })}</button>
                </fieldset>
              );
            })}
          </div>
        </fieldset>

        <fieldset className="form-section">
          <legend>{t("observationsLegend")}</legend>
          <p className="form-section__description">{t("observationsDescription")}</p>
          <button className="secondary-button" type="button" onClick={() => setObservations([...observations, { key: nextKey(), timestamp: "", returns: Object.fromEntries(components.map((component) => [component.key, ""])) }])}>{t("addObservation")}</button>
          <FieldError id="observations-error" message={errors.observations} />
          <div className="table-scroll">
            <table>
              <caption>{t("observationsLegend")}</caption>
              <thead><tr><th scope="col">#</th><th scope="col">{fields("timestamp")}</th>{components.map((component, index) => <th scope="col" key={component.key}>{fields("returnFor", { componentId: component.componentId || `${t("component")} ${index + 1}` })}</th>)}<th scope="col">{common("value")}</th></tr></thead>
              <tbody>
                {observations.map((observation, observationIndex) => (
                  <tr key={observation.key}>
                    <th scope="row">{observationIndex + 1}</th>
                    <td>
                      <label className="visually-hidden" htmlFor={`observation-${observationIndex}-timestamp`}>{fields("timestamp")}</label>
                      <input id={`observation-${observationIndex}-timestamp`} value={observation.timestamp} onChange={(event) => setObservations(observations.map((candidate) => candidate.key === observation.key ? { ...candidate, timestamp: event.target.value } : candidate))} {...fieldA11y(errors, `observation-${observationIndex}-timestamp`)} />
                      <FieldError id={`observation-${observationIndex}-timestamp-error`} message={errors[`observation-${observationIndex}-timestamp`]} />
                    </td>
                    {components.map((component, componentIndex) => {
                      const name = `observation-${observationIndex}-return-${componentIndex}`;
                      return (
                        <td key={component.key}>
                          <label className="visually-hidden" htmlFor={name}>{fields("returnFor", { componentId: component.componentId || `${t("component")} ${componentIndex + 1}` })}</label>
                          <input id={name} inputMode="decimal" value={observation.returns[component.key] ?? ""} onChange={(event) => setObservations(observations.map((candidate) => candidate.key === observation.key ? { ...candidate, returns: { ...candidate.returns, [component.key]: event.target.value } } : candidate))} {...fieldA11y(errors, name)} />
                          <FieldError id={`${name}-error`} message={errors[name]} />
                        </td>
                      );
                    })}
                    <td><button className="remove-button" type="button" disabled={observations.length <= 3} onClick={() => setObservations(observations.filter((candidate) => candidate.key !== observation.key))}>{common("remove", { item: t("observation"), number: observationIndex + 1 })}</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </fieldset>

        {([
          ["baseline", t("baselineLegend"), baseline, setBaseline, baselineTotal],
          ["proposed", t("proposedLegend"), proposed, setProposed, proposedTotal],
        ] as const).map(([kind, legend, scenario, setScenario, total]) => (
          <fieldset className="form-section" key={kind}>
            <legend>{legend}</legend>
            <p className="form-section__description">{common("weightBoundary")}</p>
            <div className="form-grid">
              <label>{fields("scenarioId")} <span className="required-label">{common("required")}</span><input value={scenario.scenarioId} onChange={(event) => setScenario({ ...scenario, scenarioId: event.target.value })} {...fieldA11y(errors, `${kind}-scenario-id`)} /><FieldError id={`${kind}-scenario-id-error`} message={errors[`${kind}-scenario-id`]} /></label>
              <label className="form-grid__wide">{fields("rationale")} <span className="required-label">{common("required")}</span><textarea value={scenario.rationale} onChange={(event) => setScenario({ ...scenario, rationale: event.target.value })} {...fieldA11y(errors, `${kind}-rationale`)} /><FieldError id={`${kind}-rationale-error`} message={errors[`${kind}-rationale`]} /></label>
            </div>
            <div className="scenario-weight-grid">
              {components.map((component, componentIndex) => {
                const name = `component-${componentIndex}-${kind}-weight`;
                const value = kind === "baseline" ? component.baselineWeight : component.proposedWeight;
                return (
                  <label key={component.key}>
                    {kind === "baseline" ? fields("baselineWeight", { componentId: component.componentId || `${t("component")} ${componentIndex + 1}` }) : fields("proposedWeight", { componentId: component.componentId || `${t("component")} ${componentIndex + 1}` })}
                    <input inputMode="decimal" value={value} onChange={(event) => setComponents(components.map((candidate) => candidate.key === component.key ? { ...candidate, [kind === "baseline" ? "baselineWeight" : "proposedWeight"]: event.target.value } : candidate))} {...fieldA11y(errors, name)} />
                    <FieldError id={`${name}-error`} message={errors[name]} />
                  </label>
                );
              })}
            </div>
            <p className="scenario-total">{total === null ? t("weightTotalInvalid") : t("weightTotal", { total: String(total) })}</p>
            <p className="field-guidance">{t("noNormalization")}</p>
            <FieldError id={`${kind}-total-error`} message={errors[`${kind}-total`]} />
            {kind === "proposed" ? (
              <label className="proposed-component-select">
                {fields("proposedComponent")} <span className="required-label">{common("required")}</span>
                <select value={proposedComponentKey} onChange={(event) => setProposedComponentKey(event.target.value)} {...fieldA11y(errors, "proposed-component")}>
                  <option value="">{fields("selectExplicitly")}</option>
                  {components.map((component, index) => <option key={component.key} value={component.componentId}>{component.componentId || `${t("component")} ${index + 1}`}</option>)}
                </select>
                <FieldError id="proposed-component-error" message={errors["proposed-component"]} />
              </label>
            ) : null}
            <StringListEditor title={common("assumptions")} item={t("assumption")} idPrefix={`${kind}-assumption`} rows={scenario.assumptions} setRows={(assumptions) => setScenario({ ...scenario, assumptions })} nextKey={nextKey} errors={errors} />
            <StringListEditor title={common("warnings")} item={t("warning")} idPrefix={`${kind}-warning`} rows={scenario.warnings} setRows={(warnings) => setScenario({ ...scenario, warnings })} nextKey={nextKey} errors={errors} />
          </fieldset>
        ))}

        <fieldset className="form-section">
          <legend>{t("analysisLegend")}</legend>
          <div className="form-grid">
            <label>{fields("analysisCreatedBy")} <span className="required-label">{common("required")}</span><input value={analysisCreatedBy} onChange={(event) => setAnalysisCreatedBy(event.target.value)} {...fieldA11y(errors, "analysis-created-by")} /><FieldError id="analysis-created-by-error" message={errors["analysis-created-by"]} /></label>
            <label>{fields("analysisCreatedTimestamp")} <span className="required-label">{common("required")}</span><input value={analysisCreatedTimestamp} onChange={(event) => setAnalysisCreatedTimestamp(event.target.value)} {...fieldA11y(errors, "analysis-created-timestamp")} /><span className="field-guidance">{common("timestampGuidance")}</span><FieldError id="analysis-created-timestamp-error" message={errors["analysis-created-timestamp"]} /></label>
          </div>
          <StringListEditor title={common("assumptions")} item={t("assumption")} idPrefix="analysis-assumption" rows={analysisAssumptions} setRows={setAnalysisAssumptions} nextKey={nextKey} errors={errors} />
          <StringListEditor title={common("warnings")} item={t("warning")} idPrefix="analysis-warning" rows={analysisWarnings} setRows={setAnalysisWarnings} nextKey={nextKey} errors={errors} />
          <StringListEditor title={common("missingEvidence")} item={t("missingEvidenceItem")} idPrefix="analysis-missing" rows={analysisMissing} setRows={setAnalysisMissing} nextKey={nextKey} errors={errors} />
        </fieldset>

        <fieldset className="form-section confirmation-panel">
          <legend>{t("confirmationLegend")}</legend>
          <label className="portfolio-confirmation">
            <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} aria-invalid={errors.confirmation ? true : undefined} aria-describedby={errors.confirmation ? "confirmation-error" : undefined} />
            <span>{t("confirmation")}</span>
          </label>
          <FieldError id="confirmation-error" message={errors.confirmation} />
        </fieldset>

        <div className="submission-actions">
          <button className="primary-button" type="submit" disabled={pending}>{pending ? t("submitting") : t("submit")}</button>
          <p>{common("historicalBoundary")}</p>
        </div>
      </form>
    </div>
  );
}
