import type {
  PortfolioReviewStatus,
} from "@/lib/api-client";

export const portfolioReviewStatuses = [
  "awaiting_decision",
  "approved",
  "rejected",
  "deferred",
] as const satisfies readonly PortfolioReviewStatus[];

export const portfolioReviewLimits = [25, 50, 100, 200] as const;

export const portfolioReviewDecisionOutcomes = [
  "approved",
  "rejected",
  "deferred",
] as const;

export const portfolioReviewEvidenceReferenceTypes = [
  "research_run",
  "configured_run",
  "backtest_artifact",
  "portfolio_artifact",
  "attribution_artifact",
  "promotion_record",
  "paper_comparison_summary",
  "paper_review_decision",
  "strategy_decision_record",
  "report_artifact_summary",
  "strategy_lifecycle_state_snapshot",
  "strategy_lifecycle_transition_record",
] as const;

export type PortfolioReviewEvidenceReferenceType =
  (typeof portfolioReviewEvidenceReferenceTypes)[number];

export const portfolioReviewResearchReferenceTypes =
  new Set<PortfolioReviewEvidenceReferenceType>([
    "research_run",
    "configured_run",
    "backtest_artifact",
    "portfolio_artifact",
    "attribution_artifact",
  ]);

const decimalTransportPattern = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/;
const timezoneSuffixPattern = /(?:Z|[+-]\d{2}:\d{2})$/;

export function parsePortfolioReviewDecimal(value: string): number | null {
  if (!decimalTransportPattern.test(value)) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function isTimezoneAwareTimestamp(value: string): boolean {
  return (
    timezoneSuffixPattern.test(value) &&
    value.trim().length === value.length &&
    Number.isFinite(Date.parse(value))
  );
}

export function scenarioWeightTotal(values: readonly string[]): number | null {
  let total = 0;
  for (const value of values) {
    const parsed = parsePortfolioReviewDecimal(value);
    if (parsed === null) {
      return null;
    }
    total += parsed;
  }
  return Number.isFinite(total) ? total : null;
}

export function acceptedScenarioWeightTotal(total: number): boolean {
  return Math.abs(total - 1) <= 1e-12;
}
