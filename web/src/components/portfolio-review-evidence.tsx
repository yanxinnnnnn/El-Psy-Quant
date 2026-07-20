"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import {
  PortfolioReviewAvailabilityValue,
  PortfolioReviewChangeValue,
} from "@/components/domain-values";
import type { PortfolioReviewDetailResponse } from "@/lib/api-client";

type Detail = PortfolioReviewDetailResponse;
type Behavior =
  Detail["analysis"]["interaction_impact_analysis"]["baseline_behavior"];
type Coverage =
  Detail["analysis"]["concentration_exposure_analysis"]["baseline_universe_coverage"];

function RawValue({ value }: { value: string | number | boolean | null }) {
  const common = useTranslations("portfolioReviews.common");
  if (value === null) return <span>{common("notAvailable")}</span>;
  return <code className="raw-value">{String(value)}</code>;
}

function RawStringList({
  values,
  empty,
}: {
  values: readonly string[] | null;
  empty?: string;
}) {
  const common = useTranslations("portfolioReviews.common");
  if (values === null) return <span>{common("notAvailable")}</span>;
  if (values.length === 0) return <span>{empty ?? common("none")}</span>;
  return (
    <ol className="raw-value-list">
      {values.map((value, index) => (
        <li key={`${index}-${value}`}><code className="raw-value">{value}</code></li>
      ))}
    </ol>
  );
}

function EvidenceSection({
  id,
  title,
  description,
  children,
}: {
  id: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="content-panel portfolio-evidence-section" id={id} aria-labelledby={`${id}-title`}>
      <div className="section-heading">
        <div><h2 id={`${id}-title`}>{title}</h2></div>
        <p>{description}</p>
      </div>
      {children}
    </section>
  );
}

function ScenarioProse({
  title,
  rationale,
  assumptions,
  warnings,
}: {
  title: string;
  rationale: string;
  assumptions: readonly string[];
  warnings: readonly string[];
}) {
  const common = useTranslations("portfolioReviews.common");
  const fields = useTranslations("portfolioReviews.fields");
  return (
    <article className="evidence-card">
      <h3>{title}</h3>
      <dl className="definition-grid">
        <div><dt>{fields("rationale")}</dt><dd>{rationale}</dd></div>
        <div><dt>{common("assumptions")}</dt><dd><RawStringList values={assumptions} /></dd></div>
        <div><dt>{common("warnings")}</dt><dd><RawStringList values={warnings} /></dd></div>
      </dl>
    </article>
  );
}

function ConcentrationTable({
  detail,
}: {
  detail: Detail;
}) {
  const t = useTranslations("portfolioReviews.detail");
  const metrics = useTranslations("portfolioReviews.metrics");
  const analysis = detail.analysis.concentration_exposure_analysis;
  const rows = [
    ["largestComponentId", analysis.baseline_concentration.largest_component_id, analysis.proposed_concentration.largest_component_id],
    ["largestComponentWeight", analysis.baseline_concentration.largest_component_weight, analysis.proposed_concentration.largest_component_weight],
    ["top3Weight", analysis.baseline_concentration.top_3_weight, analysis.proposed_concentration.top_3_weight],
    ["hhi", analysis.baseline_concentration.herfindahl_hirschman_index, analysis.proposed_concentration.herfindahl_hirschman_index],
    ["effectiveCount", analysis.baseline_concentration.effective_component_count, analysis.proposed_concentration.effective_component_count],
  ] as const;
  return (
    <div className="table-scroll">
      <table>
        <caption>{t("concentrationEvidence")}</caption>
        <thead><tr><th scope="col">{metrics("largestComponentId")}</th><th scope="col">{t("baseline")}</th><th scope="col">{t("proposed")}</th></tr></thead>
        <tbody>
          {rows.map(([key, baseline, proposed]) => (
            <tr key={key}>
              <th scope="row">{metrics(key)}</th>
              <td><RawValue value={baseline} /></td>
              <td><RawValue value={proposed} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CoverageCard({ title, value }: { title: string; value: Coverage }) {
  const metrics = useTranslations("portfolioReviews.metrics");
  const common = useTranslations("portfolioReviews.common");
  return (
    <article className="evidence-card">
      <h3>{title}</h3>
      <dl className="definition-grid">
        <div><dt>{metrics("sourceComponentCount")}</dt><dd><RawValue value={value.source_component_count} /></dd></div>
        <div><dt>{metrics("activeComponentCount")}</dt><dd><RawValue value={value.active_component_count} /></dd></div>
        <div><dt>{metrics("activeCoverageComplete")}</dt><dd>{value.active_coverage_complete ? common("yes") : common("no")} <RawValue value={value.active_coverage_complete} /></dd></div>
        <div><dt>{metrics("componentsWithEvidence")}</dt><dd><RawStringList values={value.components_with_symbol_evidence} /></dd></div>
        <div><dt>{metrics("componentsMissingEvidence")}</dt><dd><RawStringList values={value.components_missing_symbol_evidence} /></dd></div>
        <div><dt>{metrics("activeWithEvidence")}</dt><dd><RawStringList values={value.active_components_with_symbol_evidence} /></dd></div>
        <div><dt>{metrics("activeMissingEvidence")}</dt><dd><RawStringList values={value.active_components_missing_symbol_evidence} /></dd></div>
      </dl>
    </article>
  );
}

function UnavailableEvidence({
  reason,
  affected,
}: {
  reason: string;
  affected: readonly string[];
}) {
  const t = useTranslations("portfolioReviews.detail");
  const reasons = useTranslations("portfolioReviews.unavailableReasons");
  const knownReason =
    reason === "missing_symbol_evidence"
      ? reasons("missing_symbol_evidence")
      : reason === "zero_variance"
        ? reasons("zero_variance")
        : reason;
  return (
    <div className="unavailable-evidence">
      <strong>{t("unavailable")}</strong>
      <p>{knownReason}</p>
      <dl>
        <div><dt>{t("reason")}</dt><dd><RawValue value={reason} /></dd></div>
        <div><dt>{t("affectedComponents")}</dt><dd><RawStringList values={affected} /></dd></div>
      </dl>
    </div>
  );
}

const behaviorMetricKeys = [
  "observationCount",
  "periodsPerYear",
  "meanReturn",
  "sampleVolatility",
  "annualizedVolatility",
  "minReturn",
  "maxReturn",
  "positivePeriods",
  "negativePeriods",
  "zeroPeriods",
  "lossRate",
  "endingEquity",
  "cumulativeReturn",
] as const;

function behaviorValue(behavior: Behavior, key: (typeof behaviorMetricKeys)[number]) {
  const mapping = {
    observationCount: behavior.observation_count,
    periodsPerYear: behavior.periods_per_year,
    meanReturn: behavior.mean_return,
    sampleVolatility: behavior.sample_volatility,
    annualizedVolatility: behavior.annualized_volatility,
    minReturn: behavior.min_return,
    maxReturn: behavior.max_return,
    positivePeriods: behavior.positive_periods,
    negativePeriods: behavior.negative_periods,
    zeroPeriods: behavior.zero_periods,
    lossRate: behavior.loss_rate,
    endingEquity: behavior.ending_equity,
    cumulativeReturn: behavior.cumulative_return,
  } satisfies Record<(typeof behaviorMetricKeys)[number], number | null>;
  return mapping[key];
}

export function PortfolioReviewEvidence({ detail }: { detail: Detail }) {
  const t = useTranslations("portfolioReviews.detail");
  const metrics = useTranslations("portfolioReviews.metrics");
  const common = useTranslations("portfolioReviews.common");
  const fields = useTranslations("portfolioReviews.fields");
  const source = detail.source;
  const analysis = detail.analysis;
  const concentration = analysis.concentration_exposure_analysis;
  const interaction = analysis.interaction_impact_analysis;
  const baseline = analysis.baseline_scenario;
  const proposed = analysis.proposed_scenario;

  return (
    <>
      <EvidenceSection id="source" title={t("source")} description={t("componentOrder")}>
        <dl className="definition-grid definition-grid--wide">
          <div><dt>{fields("sourceId")}</dt><dd><RawValue value={source.source_id} /></dd></div>
          <div><dt>{fields("evaluationFrequency")}</dt><dd><RawValue value={source.evaluation_frequency} /></dd></div>
          <div><dt>{fields("periodsPerYear")}</dt><dd><RawValue value={source.periods_per_year} /></dd></div>
          <div><dt>{fields("createdBy")}</dt><dd><RawValue value={source.created_by} /></dd></div>
          <div><dt>{fields("createdTimestamp")}</dt><dd><RawValue value={source.created_timestamp} /></dd></div>
          <div><dt>{common("sourceDigest")}</dt><dd><RawValue value={source.source_digest} /></dd></div>
        </dl>
        <ol className="portfolio-component-inspection">
          {source.components.map((component, index) => (
            <li className="evidence-card" key={`${component.component_id}-${index}`}>
              <h3>{component.component_id}</h3>
              <dl className="definition-grid">
                <div><dt>{fields("strategyId")}</dt><dd><RawValue value={component.strategy_id} /></dd></div>
                <div><dt>{fields("label")}</dt><dd><RawValue value={component.label} /></dd></div>
                <div><dt>{fields("description")}</dt><dd><RawValue value={component.description} /></dd></div>
                <div><dt>{t("symbols")}</dt><dd><RawStringList values={component.symbols} /></dd></div>
              </dl>
              <div className="table-scroll">
                <table>
                  <caption>{t("evidenceReferences")}</caption>
                  <thead><tr><th scope="col">#</th><th scope="col">{fields("referenceType")}</th><th scope="col">{fields("referenceId")}</th><th scope="col">{fields("label")}</th><th scope="col">{fields("description")}</th><th scope="col">{common("schemaVersion")}</th></tr></thead>
                  <tbody>
                    {component.evidence_references.map((reference, referenceIndex) => (
                      <tr key={`${referenceIndex}-${reference.reference_type}-${reference.reference_id}`}>
                        <th scope="row">{referenceIndex + 1}</th>
                        <td><RawValue value={reference.reference_type} /></td>
                        <td><RawValue value={reference.reference_id} /></td>
                        <td><RawValue value={reference.label} /></td>
                        <td><RawValue value={reference.description} /></td>
                        <td><RawValue value={reference.schema_version} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </li>
          ))}
        </ol>
      </EvidenceSection>

      <EvidenceSection id="observations" title={t("observations")} description={t("fullObservations")}>
        <div className="table-scroll">
          <table>
            <caption>{t("fullObservations")}</caption>
            <thead><tr><th scope="col">#</th><th scope="col">{fields("timestamp")}</th>{source.components.map((component) => <th scope="col" key={component.component_id}>{component.component_id}</th>)}</tr></thead>
            <tbody>
              {source.return_observations.map((observation, index) => (
                <tr key={`${index}-${observation.timestamp}`}>
                  <th scope="row">{index + 1}</th>
                  <td><RawValue value={observation.timestamp} /></td>
                  {observation.component_returns.map((value, componentIndex) => <td key={`${componentIndex}-${String(value)}`}><RawValue value={value} /></td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </EvidenceSection>

      <EvidenceSection id="scenarios" title={t("scenarios")} description={t("scenarioWeights")}>
        <div className="evidence-pair">
          <ScenarioProse title={t("baseline")} rationale={baseline.rationale} assumptions={baseline.assumptions} warnings={baseline.warnings} />
          <ScenarioProse title={t("proposed")} rationale={proposed.rationale} assumptions={proposed.assumptions} warnings={proposed.warnings} />
        </div>
        <div className="table-scroll">
          <table>
            <caption>{t("scenarioWeights")}</caption>
            <thead><tr><th scope="col">{fields("componentId")}</th><th scope="col">{t("baseline")}</th><th scope="col">{t("proposed")}</th></tr></thead>
            <tbody>
              {baseline.component_weights.map((weight, index) => (
                <tr key={`${weight.component_id}-${index}`}>
                  <th scope="row">{weight.component_id}</th>
                  <td><RawValue value={weight.weight} /></td>
                  <td><RawValue value={proposed.component_weights[index]?.weight ?? null} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </EvidenceSection>

      <EvidenceSection id="concentration" title={t("concentration")} description={t("concentrationEvidence")}>
        <ConcentrationTable detail={detail} />
      </EvidenceSection>

      <EvidenceSection id="exposure" title={t("exposure")} description={t("exposureEvidence")}>
        <div className="table-scroll">
          <table>
            <caption>{t("exposureEvidence")}</caption>
            <thead><tr><th scope="col">{fields("componentId")}</th><th scope="col">{fields("strategyId")}</th><th scope="col">{fields("baselineWeight", { componentId: "" })}</th><th scope="col">{fields("proposedWeight", { componentId: "" })}</th><th scope="col">{metrics("weightDelta")}</th><th scope="col">{metrics("changeType")}</th><th scope="col">{metrics("symbolEvidenceStatus")}</th><th scope="col">{t("symbols")}</th></tr></thead>
            <tbody>
              {concentration.component_exposures.map((exposure, index) => (
                <tr key={`${exposure.component_id}-${index}`}>
                  <th scope="row">{exposure.component_id}</th>
                  <td><RawValue value={exposure.strategy_id} /></td>
                  <td><RawValue value={exposure.baseline_weight} /></td>
                  <td><RawValue value={exposure.proposed_weight} /></td>
                  <td><RawValue value={exposure.weight_delta} /></td>
                  <td><PortfolioReviewChangeValue value={exposure.change_type} /></td>
                  <td><RawValue value={exposure.symbol_evidence_status} /></td>
                  <td><RawStringList values={exposure.symbols} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="evidence-pair">
          <CoverageCard title={t("baseline")} value={concentration.baseline_universe_coverage} />
          <CoverageCard title={t("proposed")} value={concentration.proposed_universe_coverage} />
        </div>
      </EvidenceSection>

      <EvidenceSection id="overlap" title={t("overlap")} description={t("overlapEvidence")}>
        <ol className="evidence-list">
          {interaction.symbol_overlaps.map((overlap, index) => (
            <li className="evidence-card" key={`${index}-${overlap.left_component_id}-${overlap.right_component_id}`}>
              <div className="evidence-card__heading">
                <h3>{overlap.left_component_id} / {overlap.right_component_id}</h3>
                <PortfolioReviewAvailabilityValue value={overlap.status} />
              </div>
              {overlap.status === "unavailable" ? (
                <UnavailableEvidence reason={overlap.unavailable_reason ?? "missing_symbol_evidence"} affected={overlap.missing_symbol_component_ids} />
              ) : (
                <dl className="definition-grid">
                  <div><dt>{metrics("sharedSymbols")}</dt><dd><RawStringList values={overlap.shared_symbols} /></dd></div>
                  <div><dt>{metrics("sharedSymbolCount")}</dt><dd><RawValue value={overlap.shared_symbol_count} /></dd></div>
                  <div><dt>{metrics("unionSymbolCount")}</dt><dd><RawValue value={overlap.union_symbol_count} /></dd></div>
                  <div><dt>{metrics("jaccardOverlap")}</dt><dd><RawValue value={overlap.jaccard_overlap} /></dd></div>
                </dl>
              )}
            </li>
          ))}
        </ol>
      </EvidenceSection>

      <EvidenceSection id="correlation" title={t("correlation")} description={t("pairwiseEvidence")}>
        <ol className="evidence-list">
          {interaction.pairwise_correlations.map((pair, index) => (
            <li className="evidence-card" key={`${index}-${pair.left_component_id}-${pair.right_component_id}`}>
              <div className="evidence-card__heading">
                <h3>{pair.left_component_id} / {pair.right_component_id}</h3>
                <PortfolioReviewAvailabilityValue value={pair.status} />
              </div>
              {pair.status === "unavailable" ? (
                <UnavailableEvidence reason={pair.unavailable_reason ?? "zero_variance"} affected={pair.zero_variance_series} />
              ) : (
                <dl className="definition-grid">
                  <div><dt>{metrics("correlation")}</dt><dd><RawValue value={pair.correlation} /></dd></div>
                  <div><dt>{metrics("observationCount")}</dt><dd><RawValue value={pair.observation_count} /></dd></div>
                  <div><dt>{metrics("evaluationStart")}</dt><dd><RawValue value={pair.evaluation_start_timestamp} /></dd></div>
                  <div><dt>{metrics("evaluationEnd")}</dt><dd><RawValue value={pair.evaluation_end_timestamp} /></dd></div>
                </dl>
              )}
            </li>
          ))}
        </ol>
        <article className="evidence-card candidate-correlation">
          <div className="evidence-card__heading">
            <h3>{t("candidateEvidence")}</h3>
            <PortfolioReviewAvailabilityValue value={interaction.candidate_baseline_correlation.status} />
          </div>
          {interaction.candidate_baseline_correlation.status === "unavailable" ? (
            <UnavailableEvidence reason={interaction.candidate_baseline_correlation.unavailable_reason ?? "zero_variance"} affected={interaction.candidate_baseline_correlation.zero_variance_series} />
          ) : (
            <dl className="definition-grid">
              <div><dt>{metrics("candidateComponent")}</dt><dd><RawValue value={interaction.candidate_baseline_correlation.candidate_component_id} /></dd></div>
              <div><dt>{metrics("candidateBaselineWeight")}</dt><dd><RawValue value={interaction.candidate_baseline_correlation.candidate_baseline_weight} /></dd></div>
              <div><dt>{metrics("correlation")}</dt><dd><RawValue value={interaction.candidate_baseline_correlation.correlation} /></dd></div>
              <div><dt>{metrics("observationCount")}</dt><dd><RawValue value={interaction.candidate_baseline_correlation.observation_count} /></dd></div>
            </dl>
          )}
        </article>
      </EvidenceSection>

      <EvidenceSection id="behavior" title={t("behavior")} description={t("behaviorEvidence")}>
        <div className="table-scroll">
          <table>
            <caption>{t("behaviorEvidence")}</caption>
            <thead><tr><th scope="col">{common("value")}</th><th scope="col">{t("baseline")}</th><th scope="col">{t("proposed")}</th></tr></thead>
            <tbody>
              {behaviorMetricKeys.map((key) => (
                <tr key={key}><th scope="row">{metrics(key)}</th><td><RawValue value={behaviorValue(interaction.baseline_behavior, key)} /></td><td><RawValue value={behaviorValue(interaction.proposed_behavior, key)} /></td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="evidence-pair">
          {([
            [t("baseline"), interaction.baseline_behavior.worst_drawdown],
            [t("proposed"), interaction.proposed_behavior.worst_drawdown],
          ] as const).map(([title, drawdown]) => (
            <article className="evidence-card" key={title}>
              <h3>{title} · {t("drawdownEvidence")}</h3>
              <dl className="definition-grid">
                <div><dt>{metrics("maxDrawdown")}</dt><dd><RawValue value={drawdown.max_drawdown} /></dd></div>
                <div><dt>{metrics("peakDate")}</dt><dd><RawValue value={drawdown.peak_date} /></dd></div>
                <div><dt>{metrics("troughDate")}</dt><dd><RawValue value={drawdown.trough_date} /></dd></div>
                <div><dt>{metrics("recoveryDate")}</dt><dd><RawValue value={drawdown.recovery_date} /></dd></div>
                <div><dt>{metrics("recovered")}</dt><dd><RawValue value={drawdown.recovered} /></dd></div>
                <div><dt>{metrics("durationPeriods")}</dt><dd><RawValue value={drawdown.duration_periods} /></dd></div>
                <div><dt>{metrics("timeToTrough")}</dt><dd><RawValue value={drawdown.time_to_trough_periods} /></dd></div>
                <div><dt>{metrics("timeToRecovery")}</dt><dd><RawValue value={drawdown.time_to_recovery_periods} /></dd></div>
              </dl>
            </article>
          ))}
        </div>
      </EvidenceSection>

      <EvidenceSection id="contribution" title={t("contribution")} description={t("contributionEvidence")}>
        <div className="table-scroll">
          <table>
            <caption>{t("contributionEvidence")}</caption>
            <thead><tr><th scope="col">{fields("componentId")}</th><th scope="col">{t("baseline")} · {metrics("totalContribution")}</th><th scope="col">{t("proposed")} · {metrics("totalContribution")}</th><th scope="col">{t("baseline")} · {metrics("meanContribution")}</th><th scope="col">{t("proposed")} · {metrics("meanContribution")}</th></tr></thead>
            <tbody>
              {interaction.baseline_behavior.component_contributions.map((item, index) => {
                const proposedItem = interaction.proposed_behavior.component_contributions[index];
                return (
                  <tr key={`${item.component_id}-${index}`}>
                    <th scope="row">{item.component_id}</th>
                    <td><RawValue value={item.total_contribution} /></td>
                    <td><RawValue value={proposedItem?.total_contribution ?? null} /></td>
                    <td><RawValue value={item.mean_contribution} /></td>
                    <td><RawValue value={proposedItem?.mean_contribution ?? null} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </EvidenceSection>

      <EvidenceSection id="impact" title={t("impact")} description={t("impactEvidence")}>
        <dl className="definition-grid definition-grid--wide evidence-card">
          {([
            ["meanReturnDelta", interaction.proposed_impact.mean_return_delta],
            ["sampleVolatilityDelta", interaction.proposed_impact.sample_volatility_delta],
            ["annualizedVolatilityDelta", interaction.proposed_impact.annualized_volatility_delta],
            ["minReturnDelta", interaction.proposed_impact.min_return_delta],
            ["maxReturnDelta", interaction.proposed_impact.max_return_delta],
            ["positivePeriodsDelta", interaction.proposed_impact.positive_periods_delta],
            ["negativePeriodsDelta", interaction.proposed_impact.negative_periods_delta],
            ["zeroPeriodsDelta", interaction.proposed_impact.zero_periods_delta],
            ["lossRateDelta", interaction.proposed_impact.loss_rate_delta],
            ["endingEquityDelta", interaction.proposed_impact.ending_equity_delta],
            ["cumulativeReturnDelta", interaction.proposed_impact.cumulative_return_delta],
            ["maxDrawdownDelta", interaction.proposed_impact.max_drawdown_delta],
          ] as const).map(([key, value]) => <div key={key}><dt>{metrics(key)}</dt><dd><RawValue value={value} /></dd></div>)}
        </dl>
        <div className="table-scroll">
          <table>
            <caption>{t("contributionImpactEvidence")}</caption>
            <thead><tr><th scope="col">{fields("componentId")}</th><th scope="col">{metrics("totalContributionDelta")}</th><th scope="col">{metrics("meanContributionDelta")}</th><th scope="col">{metrics("positivePeriodsDelta")}</th><th scope="col">{metrics("negativePeriodsDelta")}</th><th scope="col">{metrics("zeroPeriodsDelta")}</th></tr></thead>
            <tbody>
              {interaction.component_contribution_impacts.map((item, index) => (
                <tr key={`${item.component_id}-${index}`}>
                  <th scope="row">{item.component_id}</th>
                  <td><RawValue value={item.total_contribution_delta} /></td>
                  <td><RawValue value={item.mean_contribution_delta} /></td>
                  <td><RawValue value={item.positive_periods_delta} /></td>
                  <td><RawValue value={item.negative_periods_delta} /></td>
                  <td><RawValue value={item.zero_periods_delta} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </EvidenceSection>

      <EvidenceSection id="limitations" title={t("limitations")} description={t("proseOrder")}>
        <div className="evidence-prose-grid">
          {([
            ["Source", source.assumptions, source.warnings, source.missing_evidence],
            [t("baseline"), baseline.assumptions, baseline.warnings, []],
            [t("proposed"), proposed.assumptions, proposed.warnings, []],
            ["Analysis", analysis.assumptions, analysis.warnings, analysis.missing_evidence],
          ] as const).map(([title, assumptions, warnings, missing]) => (
            <article className="evidence-card" key={title}>
              <h3>{title}</h3>
              <dl className="definition-grid">
                <div><dt>{common("assumptions")}</dt><dd><RawStringList values={assumptions} /></dd></div>
                <div><dt>{common("warnings")}</dt><dd><RawStringList values={warnings} /></dd></div>
                <div><dt>{common("missingEvidence")}</dt><dd><RawStringList values={missing} /></dd></div>
              </dl>
            </article>
          ))}
        </div>
      </EvidenceSection>
    </>
  );
}
