import commonEn from "../../messages/en/common.json";
import comparisonsEn from "../../messages/en/comparisons.json";
import errorsEn from "../../messages/en/errors.json";
import evidenceEn from "../../messages/en/evidence.json";
import lifecycleEn from "../../messages/en/lifecycle.json";
import marketTimeEn from "../../messages/en/market-time.json";
import navigationEn from "../../messages/en/navigation.json";
import overviewEn from "../../messages/en/overview.json";
import paperAccountsEn from "../../messages/en/paper-accounts.json";
import paperJobsEn from "../../messages/en/paper-jobs.json";
import paperExecutionEn from "../../messages/en/paper-execution.json";
import paperRuntimesEn from "../../messages/en/paper-runtimes.json";
import portfolioRecordsEn from "../../messages/en/portfolio-records.json";
import portfolioReviewsEn from "../../messages/en/portfolio-reviews.json";
import researchEn from "../../messages/en/research.json";
import strategiesEn from "../../messages/en/strategies.json";
import strategyToRiskEn from "../../messages/en/strategy-to-risk.json";
import commonZhCn from "../../messages/zh-CN/common.json";
import comparisonsZhCn from "../../messages/zh-CN/comparisons.json";
import errorsZhCn from "../../messages/zh-CN/errors.json";
import evidenceZhCn from "../../messages/zh-CN/evidence.json";
import lifecycleZhCn from "../../messages/zh-CN/lifecycle.json";
import marketTimeZhCn from "../../messages/zh-CN/market-time.json";
import navigationZhCn from "../../messages/zh-CN/navigation.json";
import overviewZhCn from "../../messages/zh-CN/overview.json";
import paperAccountsZhCn from "../../messages/zh-CN/paper-accounts.json";
import paperJobsZhCn from "../../messages/zh-CN/paper-jobs.json";
import paperExecutionZhCn from "../../messages/zh-CN/paper-execution.json";
import paperRuntimesZhCn from "../../messages/zh-CN/paper-runtimes.json";
import portfolioRecordsZhCn from "../../messages/zh-CN/portfolio-records.json";
import portfolioReviewsZhCn from "../../messages/zh-CN/portfolio-reviews.json";
import researchZhCn from "../../messages/zh-CN/research.json";
import strategiesZhCn from "../../messages/zh-CN/strategies.json";
import strategyToRiskZhCn from "../../messages/zh-CN/strategy-to-risk.json";

import { FALLBACK_LOCALE, type Locale } from "@/i18n/config";

const EN_MESSAGES = {
  common: commonEn,
  navigation: navigationEn,
  overview: overviewEn,
  strategies: strategiesEn,
  research: researchEn,
  evidence: evidenceEn,
  paperJobs: paperJobsEn,
  portfolioRecords: portfolioRecordsEn,
  comparisons: comparisonsEn,
  portfolioReviews: portfolioReviewsEn,
  paperAccounts: paperAccountsEn,
  marketTime: marketTimeEn,
  strategyToRisk: strategyToRiskEn,
  paperExecution: paperExecutionEn,
  paperRuntimes: paperRuntimesEn,
  lifecycle: lifecycleEn,
  errors: errorsEn,
} as const;

const ZH_CN_MESSAGES: typeof EN_MESSAGES = {
  common: commonZhCn,
  navigation: navigationZhCn,
  overview: overviewZhCn,
  strategies: strategiesZhCn,
  research: researchZhCn,
  evidence: evidenceZhCn,
  paperJobs: paperJobsZhCn,
  portfolioRecords: portfolioRecordsZhCn,
  comparisons: comparisonsZhCn,
  portfolioReviews: portfolioReviewsZhCn,
  paperAccounts: paperAccountsZhCn,
  marketTime: marketTimeZhCn,
  strategyToRisk: strategyToRiskZhCn,
  paperExecution: paperExecutionZhCn,
  paperRuntimes: paperRuntimesZhCn,
  lifecycle: lifecycleZhCn,
  errors: errorsZhCn,
};

const STATIC_MESSAGES: Readonly<Record<Locale, typeof EN_MESSAGES>> = {
  en: EN_MESSAGES,
  "zh-CN": ZH_CN_MESSAGES,
};

export type AppMessages = typeof EN_MESSAGES;

export function loadMessages(locale: Locale): AppMessages {
  return STATIC_MESSAGES[locale] ?? STATIC_MESSAGES[FALLBACK_LOCALE];
}
