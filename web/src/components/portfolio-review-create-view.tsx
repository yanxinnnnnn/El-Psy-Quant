"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useRef, useState } from "react";

import { ErrorState, RequestId } from "@/components/data-states";
import { useWorkspaceEnvironment } from "@/components/workspace-shell";
import {
  ApiClientError,
  createPortfolioReview,
  fetchEvidenceManifestDetail,
  fetchEvidenceManifests,
  fetchResearchRuns,
  isPortfolioReviewCreateRequest,
  type ApiResult,
  type EvidenceManifestDetailResponse,
  type EvidenceManifestListResponse,
  type PortfolioReviewCommandResponse,
  type PortfolioReviewCreateRequest,
  type ResearchRunListResponse,
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
type PreservedRead<Data> = {
  data: Data | null;
  loading: boolean;
  failure: Failure | null;
  refresh: () => void;
};

function usePreservedRead<Data>(
  request: () => Promise<ApiResult<Data>>,
): PreservedRead<Data> {
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [failure, setFailure] = useState<Failure | null>(null);
  const sequence = useRef(0);
  const refresh = useCallback(() => {
    const current = ++sequence.current;
    setLoading(true);
    setFailure(null);
    void request()
      .then((result) => {
        if (current === sequence.current) setData(result.data);
      })
      .catch((error: unknown) => {
        if (current === sequence.current) setFailure(failureFrom(error));
      })
      .finally(() => {
        if (current === sequence.current) setLoading(false);
      });
  }, [request]);
  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (active) refresh();
    });
    return () => {
      active = false;
      sequence.current += 1;
    };
  }, [refresh]);
  return { data, loading, failure, refresh };
}

function manifestReferenceGroups(detail: EvidenceManifestDetailResponse) {
  if (detail.manifest_type === "strategy_decision_manifest") {
    return [
      ["summary_references", detail.summary_references],
      ["record_references", detail.record_references],
    ] as const;
  }
  if (detail.manifest_type === "report_artifact_manifest") {
    return [["references", detail.references]] as const;
  }
  return [
    ["state_snapshot_references", detail.state_snapshot_references],
    ["transition_proposal_references", detail.transition_proposal_references],
    ["transition_record_references", detail.transition_record_references],
  ] as const;
}

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
  const integration = useTranslations("portfolioReviews.integration");
  const environment = useWorkspaceEnvironment();
  const researchRequest = useCallback(() => fetchResearchRuns(), []);
  const evidenceRequest = useCallback(() => fetchEvidenceManifests(), []);
  const research = usePreservedRead<ResearchRunListResponse>(researchRequest);
  const evidence = usePreservedRead<EvidenceManifestListResponse>(evidenceRequest);
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
  const [integrationTargetKey, setIntegrationTargetKey] = useState("");
  const [selectedResearchIdentity, setSelectedResearchIdentity] = useState("");
  const [selectedManifestIdentity, setSelectedManifestIdentity] = useState("");
  const [manifestDetail, setManifestDetail] =
    useState<EvidenceManifestDetailResponse | null>(null);
  const [manifestDetailLoading, setManifestDetailLoading] = useState(false);
  const [manifestDetailFailure, setManifestDetailFailure] =
    useState<Failure | null>(null);
  const manifestSequence = useRef(0);
  const [selectedManifestReferences, setSelectedManifestReferences] =
    useState<string[]>([]);
  const [integrationNotice, setIntegrationNotice] = useState<string | null>(null);
  const [demoReplaceConfirmed, setDemoReplaceConfirmed] = useState(false);
  const [demoLoadFailure, setDemoLoadFailure] = useState<Failure | null>(null);

  function targetComponent(): ComponentRow | null {
    const key = Number(integrationTargetKey);
    return components.find((component) => component.key === key) ?? null;
  }

  function selectedResearchRun() {
    return research.data?.runs.find(
      (run) => `${run.experiment_slug}\u0000${run.run_id}` === selectedResearchIdentity,
    ) ?? null;
  }

  function researchEvidence(run: ResearchRunListResponse["runs"][number]): EvidenceRow {
    return {
      key: nextKey(),
      referenceType: "research_run",
      referenceId: `${run.experiment_slug}/${run.run_id}`,
      label: "",
      description: "",
    };
  }

  function addSelectedResearchComponent() {
    const run = selectedResearchRun();
    if (run === null || components.length >= 12) {
      setIntegrationNotice(integration("selectResearchFirst"));
      return;
    }
    const key = nextKey();
    setComponents([...components, {
      key,
      componentId: "",
      strategyId: run.strategy,
      label: run.experiment_name,
      description: "",
      evidence: [researchEvidence(run)],
      symbols: run.symbols.map((value) => ({ key: nextKey(), value })),
      baselineWeight: "",
      proposedWeight: "",
    }]);
    setObservations(observations.map((row) => ({
      ...row,
      returns: { ...row.returns, [key]: "" },
    })));
    setIntegrationNotice(integration("researchAdded"));
  }

  function applySelectedResearchToTarget() {
    const run = selectedResearchRun();
    const target = targetComponent();
    if (run === null || target === null) {
      setIntegrationNotice(integration("selectResearchAndTarget"));
      return;
    }
    const referenceId = `${run.experiment_slug}/${run.run_id}`;
    if (target.evidence.some((reference) =>
      reference.referenceType === "research_run" &&
      reference.referenceId === referenceId
    )) {
      setIntegrationNotice(integration("duplicateRefused"));
      return;
    }
    setComponents(components.map((component) =>
      component.key === target.key
        ? {
            ...component,
            strategyId: run.strategy,
            label: run.experiment_name,
            symbols: run.symbols.map((value) => ({ key: nextKey(), value })),
            evidence: [...component.evidence, researchEvidence(run)],
          }
        : component
    ));
    setIntegrationNotice(integration("researchApplied"));
  }

  function loadManifestDetail(identity = selectedManifestIdentity) {
    const [manifestType, artifactKey] = identity.split("\u0000");
    if (!manifestType || !artifactKey) return;
    const current = ++manifestSequence.current;
    setManifestDetailLoading(true);
    setManifestDetailFailure(null);
    setSelectedManifestReferences([]);
    void fetchEvidenceManifestDetail(manifestType, artifactKey)
      .then((response) => {
        if (current === manifestSequence.current) setManifestDetail(response.data);
      })
      .catch((error: unknown) => {
        if (current === manifestSequence.current) {
          setManifestDetailFailure(failureFrom(error));
        }
      })
      .finally(() => {
        if (current === manifestSequence.current) setManifestDetailLoading(false);
      });
  }

  function addSelectedManifestReferences() {
    const target = targetComponent();
    if (target === null || manifestDetail === null || selectedManifestReferences.length === 0) {
      setIntegrationNotice(integration("selectManifestRefsAndTarget"));
      return;
    }
    const selected = new Set(selectedManifestReferences);
    const additions: EvidenceRow[] = [];
    for (const [groupName, references] of manifestReferenceGroups(manifestDetail)) {
      references.forEach((reference, index) => {
        const key = `${groupName}\u0000${index}`;
        if (!selected.has(key)) return;
        if (!portfolioReviewEvidenceReferenceTypes.includes(
          reference.reference_type as PortfolioReviewEvidenceReferenceType,
        )) return;
        additions.push({
          key: nextKey(),
          referenceType: reference.reference_type as PortfolioReviewEvidenceReferenceType,
          referenceId: reference.reference_id,
          label: reference.label ?? "",
          description: reference.description ?? "",
        });
      });
    }
    const identities = new Set(target.evidence.map((reference) =>
      `${reference.referenceType}\u0000${reference.referenceId}`
    ));
    const additionIdentities = additions.map((reference) =>
      `${reference.referenceType}\u0000${reference.referenceId}`
    );
    if (
      new Set(additionIdentities).size !== additionIdentities.length ||
      additionIdentities.some((identity) => identities.has(identity))
    ) {
      setIntegrationNotice(integration("duplicateRefused"));
      return;
    }
    setComponents(components.map((component) =>
      component.key === target.key
        ? { ...component, evidence: [...component.evidence, ...additions] }
        : component
    ));
    setIntegrationNotice(integration("manifestReferencesAdded", { count: additions.length }));
  }

  function applyCreateRequest(
    request: PortfolioReviewCreateRequest,
    createIdempotencyKey: string,
  ) {
    const componentKeys = request.source.components.map(() => nextKey());
    setReviewId(request.review_id);
    setIdempotencyKey(createIdempotencyKey);
    setSourceId(request.source.source_id);
    setSourceCreatedBy(request.source.created_by);
    setSourceCreatedTimestamp(request.source.created_timestamp);
    setEvaluationFrequency(request.source.evaluation_frequency);
    setPeriodsPerYear(request.source.periods_per_year === null
      ? ""
      : String(request.source.periods_per_year));
    const rows = (values: string[]) => values.map((value) => ({ key: nextKey(), value }));
    setSourceAssumptions(rows(request.source.assumptions));
    setSourceWarnings(rows(request.source.warnings));
    setSourceMissing(rows(request.source.missing_evidence));
    setComponents(request.source.components.map((component, index) => ({
      key: componentKeys[index],
      componentId: component.component_id,
      strategyId: component.strategy_id,
      label: component.label ?? "",
      description: component.description ?? "",
      evidence: component.evidence_references.map((reference) => ({
        key: nextKey(),
        referenceType: reference.reference_type as PortfolioReviewEvidenceReferenceType,
        referenceId: reference.reference_id,
        label: reference.label ?? "",
        description: reference.description ?? "",
      })),
      symbols: rows(component.symbols ?? []),
      baselineWeight: String(request.baseline_scenario.weights[component.component_id]),
      proposedWeight: String(request.proposed_scenario.weights[component.component_id]),
    })));
    setObservations(request.source.return_observations.map((observation) => ({
      key: nextKey(),
      timestamp: observation.timestamp,
      returns: Object.fromEntries(componentKeys.map((key, index) => [
        key,
        String(observation.component_returns[index]),
      ])),
    })));
    setBaseline({
      scenarioId: request.baseline_scenario.scenario_id,
      rationale: request.baseline_scenario.rationale,
      assumptions: rows(request.baseline_scenario.assumptions),
      warnings: rows(request.baseline_scenario.warnings),
    });
    setProposed({
      scenarioId: request.proposed_scenario.scenario_id,
      rationale: request.proposed_scenario.rationale,
      assumptions: rows(request.proposed_scenario.assumptions),
      warnings: rows(request.proposed_scenario.warnings),
    });
    setProposedComponentKey(request.proposed_scenario.proposed_component_id);
    setAnalysisCreatedBy(request.analysis.created_by);
    setAnalysisCreatedTimestamp(request.analysis.created_timestamp);
    setAnalysisAssumptions(rows(request.analysis.assumptions));
    setAnalysisWarnings(rows(request.analysis.warnings));
    setAnalysisMissing(rows(request.analysis.missing_evidence));
    setConfirmed(false);
    setErrors({});
    setServerError(null);
    setResult(null);
    setDemoLoadFailure(null);
    setIntegrationNotice(integration("demoLoaded"));
  }

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

        {environment.state.status === "success" ? (
          <fieldset className="form-section demo-portfolio-loader">
            <legend>{integration("demoTitle")}</legend>
            <p className="form-section__description">{integration("demoDescription")}</p>
            {demoLoadFailure ? (
              <ErrorState
                code={demoLoadFailure.code}
                title={integration("demoInvalid")}
                message={demoLoadFailure.message}
                requestId={demoLoadFailure.requestId}
                httpStatus={demoLoadFailure.httpStatus}
                operation="demo_workspace.read"
              />
            ) : null}
            <label className="portfolio-confirmation">
              <input
                type="checkbox"
                checked={demoReplaceConfirmed}
                onChange={(event) => setDemoReplaceConfirmed(event.target.checked)}
              />
              <span>{integration("demoReplaceConfirmation")}</span>
            </label>
            <button
              className="secondary-button"
              type="button"
              disabled={!demoReplaceConfirmed}
              onClick={() => {
                const example = environment.state.status === "success"
                  ? environment.state.data.portfolio_review_example
                  : null;
                if (example === null || !isPortfolioReviewCreateRequest(example.request)) {
                  setDemoLoadFailure({
                    code: "api_response_invalid",
                    message: integration("demoInvalid"),
                    requestId: environment.state.status === "success"
                      ? environment.state.requestId
                      : null,
                    httpStatus: null,
                  });
                  return;
                }
                applyCreateRequest(example.request, example.create_idempotency_key);
                setDemoReplaceConfirmed(false);
              }}
            >
              {integration("demoLoad")}
            </button>
          </fieldset>
        ) : environment.state.status === "error" &&
          environment.state.code !== "demo_workspace_not_configured" ? (
          <ErrorState
            className="form-alert form-alert--server"
            code={environment.state.code}
            title={integration("demoUnavailable")}
            message={environment.state.message}
            requestId={environment.state.requestId}
            httpStatus={environment.state.httpStatus}
            operation="demo_workspace.read"
            onRetry={environment.retry}
            retryLabel={integration("retry")}
          />
        ) : null}

        <fieldset className="form-section portfolio-source-integration">
          <legend>{integration("title")}</legend>
          <p className="form-section__description">{integration("description")}</p>
          <p className="neutral-note">{integration("returnsRemainManual")}</p>
          <label>
            {integration("targetComponent")}
            <select
              value={integrationTargetKey}
              onChange={(event) => setIntegrationTargetKey(event.target.value)}
            >
              <option value="">{fields("selectExplicitly")}</option>
              {components.map((component, index) => (
                <option key={component.key} value={String(component.key)}>
                  {component.componentId || `${t("component")} ${index + 1}`}
                </option>
              ))}
            </select>
          </label>
          {integrationNotice ? <p className="mutation-notice" role="status">{integrationNotice}</p> : null}

          <section aria-labelledby="portfolio-research-picker-title">
            <div className="repeatable-heading">
              <div>
                <h3 id="portfolio-research-picker-title">{integration("researchTitle")}</h3>
                <p>{integration("researchDescription")}</p>
              </div>
              <button className="quiet-button" type="button" onClick={research.refresh} disabled={research.loading}>
                {research.loading ? integration("refreshing") : integration("refresh")}
              </button>
            </div>
            {research.failure ? (
              <ErrorState
                code={research.failure.code}
                title={integration("researchUnavailable")}
                message={research.failure.message}
                requestId={research.failure.requestId}
                httpStatus={research.failure.httpStatus}
                operation="research_run.list"
                onRetry={research.refresh}
                retryLabel={integration("retry")}
              />
            ) : null}
            {research.loading && research.data === null ? (
              <p role="status">{integration("researchLoading")}</p>
            ) : research.data?.runs.length === 0 ? (
              <p>{integration("researchEmpty")}</p>
            ) : research.data ? (
              <>
                <label>
                  {integration("researchSelect")}
                  <select
                    value={selectedResearchIdentity}
                    onChange={(event) => setSelectedResearchIdentity(event.target.value)}
                  >
                    <option value="">{fields("selectExplicitly")}</option>
                    {research.data.runs.map((run, index) => (
                      <option
                        key={`${run.experiment_slug}-${run.run_id}-${index}`}
                        value={`${run.experiment_slug}\u0000${run.run_id}`}
                      >
                        {run.experiment_name} — {run.experiment_slug}/{run.run_id}
                      </option>
                    ))}
                  </select>
                </label>
                {selectedResearchRun() ? (
                  <div className="integration-selection-card">
                    <code>{selectedResearchRun()?.experiment_slug}/{selectedResearchRun()?.run_id}</code>
                    <p>{selectedResearchRun()?.strategy}</p>
                    <p>{selectedResearchRun()?.symbols.join(" · ")}</p>
                    <Link
                      className="text-link"
                      target="_blank"
                      rel="noreferrer"
                      href={`/research-runs/${encodeURIComponent(selectedResearchRun()?.experiment_slug ?? "")}/${encodeURIComponent(selectedResearchRun()?.run_id ?? "")}`}
                    >
                      {integration("inspectResearch")}
                    </Link>
                  </div>
                ) : null}
                <div className="submission-actions">
                  <button className="secondary-button" type="button" onClick={addSelectedResearchComponent} disabled={components.length >= 12}>
                    {integration("addResearchComponent")}
                  </button>
                  <button className="secondary-button" type="button" onClick={applySelectedResearchToTarget}>
                    {integration("applyResearchTarget")}
                  </button>
                </div>
              </>
            ) : null}
          </section>

          <section aria-labelledby="portfolio-manifest-picker-title">
            <div className="repeatable-heading">
              <div>
                <h3 id="portfolio-manifest-picker-title">{integration("manifestTitle")}</h3>
                <p>{integration("manifestDescription")}</p>
              </div>
              <button className="quiet-button" type="button" onClick={evidence.refresh} disabled={evidence.loading}>
                {evidence.loading ? integration("refreshing") : integration("refresh")}
              </button>
            </div>
            {evidence.failure ? (
              <ErrorState
                code={evidence.failure.code}
                title={integration("manifestUnavailable")}
                message={evidence.failure.message}
                requestId={evidence.failure.requestId}
                httpStatus={evidence.failure.httpStatus}
                operation="evidence_manifest.list"
                onRetry={evidence.refresh}
                retryLabel={integration("retry")}
              />
            ) : null}
            {evidence.loading && evidence.data === null ? (
              <p role="status">{integration("manifestLoading")}</p>
            ) : evidence.data?.manifests.length === 0 ? (
              <p>{integration("manifestEmpty")}</p>
            ) : evidence.data ? (
              <label>
                {integration("manifestSelect")}
                <select
                  value={selectedManifestIdentity}
                  onChange={(event) => {
                    const identity = event.target.value;
                    setSelectedManifestIdentity(identity);
                    if (identity) loadManifestDetail(identity);
                  }}
                >
                  <option value="">{fields("selectExplicitly")}</option>
                  {evidence.data.manifests.map((manifest, index) => (
                    <option
                      key={`${manifest.manifest_type}-${manifest.artifact_key}-${index}`}
                      value={`${manifest.manifest_type}\u0000${manifest.artifact_key}`}
                    >
                      {manifest.manifest_type} / {manifest.artifact_key} / {manifest.manifest_id}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            {selectedManifestIdentity ? (
              <button className="quiet-button" type="button" onClick={() => loadManifestDetail()} disabled={manifestDetailLoading}>
                {manifestDetailLoading ? integration("refreshing") : integration("refreshDetail")}
              </button>
            ) : null}
            {manifestDetailFailure ? (
              <ErrorState
                code={manifestDetailFailure.code}
                title={integration("manifestDetailUnavailable")}
                message={manifestDetailFailure.message}
                requestId={manifestDetailFailure.requestId}
                httpStatus={manifestDetailFailure.httpStatus}
                operation="evidence_manifest.detail"
                onRetry={() => loadManifestDetail()}
                retryLabel={integration("retry")}
              />
            ) : null}
            {manifestDetail ? (
              <div className="manifest-reference-picker">
                <dl className="compact-definitions">
                  <div><dt>{integration("manifestType")}</dt><dd><code>{manifestDetail.manifest_type}</code></dd></div>
                  <div><dt>{integration("artifactKey")}</dt><dd><code>{manifestDetail.artifact_key}</code></dd></div>
                  <div><dt>{integration("manifestId")}</dt><dd><code>{manifestDetail.manifest_id}</code></dd></div>
                </dl>
                {manifestReferenceGroups(manifestDetail).map(([groupName, references]) => (
                  <fieldset key={groupName}>
                    <legend><code>{groupName}</code></legend>
                    {references.map((reference, index) => {
                      const key = `${groupName}\u0000${index}`;
                      const supported = portfolioReviewEvidenceReferenceTypes.includes(
                        reference.reference_type as PortfolioReviewEvidenceReferenceType,
                      );
                      return (
                        <label className="portfolio-confirmation" key={key}>
                          <input
                            type="checkbox"
                            disabled={!supported}
                            checked={selectedManifestReferences.includes(key)}
                            onChange={(event) => setSelectedManifestReferences(
                              event.target.checked
                                ? [...selectedManifestReferences, key]
                                : selectedManifestReferences.filter((item) => item !== key),
                            )}
                          />
                          <span>
                            <code>{reference.reference_type}</code> / <code>{reference.reference_id}</code>
                            <span>{reference.label ?? common("notAvailable")}</span>
                            <span>{reference.description ?? common("notAvailable")}</span>
                            <strong>{supported ? integration("supported") : integration("unsupported")}</strong>
                          </span>
                        </label>
                      );
                    })}
                  </fieldset>
                ))}
                <button className="secondary-button" type="button" onClick={addSelectedManifestReferences}>
                  {integration("addSelectedReferences")}
                </button>
              </div>
            ) : null}
          </section>
        </fieldset>

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
