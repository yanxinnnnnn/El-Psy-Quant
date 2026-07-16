import commonEn from "../../messages/en/common.json";
import comparisonsEn from "../../messages/en/comparisons.json";
import errorsEn from "../../messages/en/errors.json";
import evidenceEn from "../../messages/en/evidence.json";
import lifecycleEn from "../../messages/en/lifecycle.json";
import navigationEn from "../../messages/en/navigation.json";
import overviewEn from "../../messages/en/overview.json";
import paperJobsEn from "../../messages/en/paper-jobs.json";
import portfolioRecordsEn from "../../messages/en/portfolio-records.json";
import researchEn from "../../messages/en/research.json";
import strategiesEn from "../../messages/en/strategies.json";
import commonZhCn from "../../messages/zh-CN/common.json";
import comparisonsZhCn from "../../messages/zh-CN/comparisons.json";
import errorsZhCn from "../../messages/zh-CN/errors.json";
import evidenceZhCn from "../../messages/zh-CN/evidence.json";
import lifecycleZhCn from "../../messages/zh-CN/lifecycle.json";
import navigationZhCn from "../../messages/zh-CN/navigation.json";
import overviewZhCn from "../../messages/zh-CN/overview.json";
import paperJobsZhCn from "../../messages/zh-CN/paper-jobs.json";
import portfolioRecordsZhCn from "../../messages/zh-CN/portfolio-records.json";
import researchZhCn from "../../messages/zh-CN/research.json";
import strategiesZhCn from "../../messages/zh-CN/strategies.json";

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
