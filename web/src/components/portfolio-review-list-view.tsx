"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/data-states";
import { PortfolioReviewStatusValue } from "@/components/domain-values";
import { LocalizedTimestamp } from "@/components/localized-values";
import {
  fetchPortfolioReviews,
  type PortfolioReviewListResponse,
  type PortfolioReviewStatus,
} from "@/lib/api-client";
import {
  portfolioReviewLimits,
  portfolioReviewStatuses,
} from "@/lib/portfolio-reviews";
import {
  type SettledApiResourceState,
  useApiResource,
} from "@/lib/use-api-resource";

function ReviewCard({
  review,
}: {
  review: PortfolioReviewListResponse[number];
}) {
  const t = useTranslations("portfolioReviews.list");
  const common = useTranslations("portfolioReviews.common");
  return (
    <li className="record-card portfolio-review-card">
      <div>
        <p className="record-card__meta">{review.review_id}</p>
        <h2>{review.source_id}</h2>
        <dl className="compact-definitions portfolio-review-card__definitions">
          <div>
            <dt>{t("reviewId")}</dt>
            <dd><code className="raw-value">{review.review_id}</code></dd>
          </div>
          <div>
            <dt>{t("sourceId")}</dt>
            <dd><code className="raw-value">{review.source_id}</code></dd>
          </div>
          <div>
            <dt>{t("proposedComponentId")}</dt>
            <dd><code className="raw-value">{review.proposed_component_id}</code></dd>
          </div>
          <div>
            <dt>{t("status")}</dt>
            <dd><PortfolioReviewStatusValue value={review.status} /></dd>
          </div>
          <div>
            <dt>{t("created")}</dt>
            <dd><LocalizedTimestamp value={review.created_timestamp} /></dd>
          </div>
          <div>
            <dt>{t("updated")}</dt>
            <dd><LocalizedTimestamp value={review.updated_timestamp} /></dd>
          </div>
          <div>
            <dt>{t("reviewed")}</dt>
            <dd>
              {review.reviewed_timestamp === null
                ? common("notAvailable")
                : <LocalizedTimestamp value={review.reviewed_timestamp} />}
            </dd>
          </div>
          <div className="portfolio-review-card__digest">
            <dt>{common("analysisDigest")}</dt>
            <dd><code className="raw-value">{review.analysis_digest}</code></dd>
          </div>
        </dl>
      </div>
      <Link
        className="primary-link"
        href={`/portfolio-reviews/${encodeURIComponent(review.review_id)}`}
      >
        {t("inspect")}
      </Link>
    </li>
  );
}

function settledData(
  state: SettledApiResourceState<PortfolioReviewListResponse> | null,
): PortfolioReviewListResponse | null {
  return state?.status === "success" ? state.data : null;
}

export function PortfolioReviewListView() {
  const t = useTranslations("portfolioReviews.list");
  const statuses = useTranslations("portfolioReviews.statuses");
  const common = useTranslations("portfolioReviews.common");
  const [draftStatus, setDraftStatus] =
    useState<PortfolioReviewStatus | "all">("all");
  const [draftLimit, setDraftLimit] =
    useState<(typeof portfolioReviewLimits)[number]>(50);
  const [filters, setFilters] = useState<{
    status: PortfolioReviewStatus | null;
    limit: (typeof portfolioReviewLimits)[number];
  }>({ status: null, limit: 50 });
  const request = useCallback(() => fetchPortfolioReviews(filters), [filters]);
  const { state, retry } = useApiResource(request);
  const previous =
    state.status === "loading" ? settledData(state.previous) : null;
  const reviews =
    state.status === "success"
      ? state.data
      : previous;
  const refreshPending = state.status === "loading" && previous !== null;

  return (
    <div className="business-workspace">
      <header className="page-heading page-heading--with-action">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p>{t("description")}</p>
        </div>
        <Link className="primary-link" href="/portfolio-reviews/new">
          {t("create")}
        </Link>
      </header>

      <form
        className="filter-bar"
        aria-label={t("filtersAria")}
        onSubmit={(event) => {
          event.preventDefault();
          setFilters({
            status: draftStatus === "all" ? null : draftStatus,
            limit: draftLimit,
          });
        }}
      >
        <label>
          {t("status")}
          <select
            value={draftStatus}
            onChange={(event) =>
              setDraftStatus(event.target.value as PortfolioReviewStatus | "all")
            }
          >
            <option value="all">{t("allStatuses")}</option>
            {portfolioReviewStatuses.map((status) => (
              <option key={status} value={status}>
                {statuses(status)} ({status})
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("limit")}
          <select
            value={draftLimit}
            onChange={(event) =>
              setDraftLimit(
                Number(event.target.value) as
                  (typeof portfolioReviewLimits)[number],
              )
            }
          >
            {portfolioReviewLimits.map((limit) => (
              <option key={limit} value={limit}>{limit}</option>
            ))}
          </select>
        </label>
        <button className="secondary-button" type="submit">{t("apply")}</button>
        <button className="secondary-button" type="button" onClick={retry}>
          {t("refresh")}
        </button>
      </form>

      {refreshPending ? (
        <p className="neutral-note" role="status" aria-live="polite">
          {common("refreshing")}
        </p>
      ) : null}
      {state.status === "loading" && reviews === null ? (
        <LoadingState message={t("loading")} />
      ) : state.status === "error" ? (
        <ErrorState
          code={state.code}
          title={t("unavailableTitle")}
          message={state.message}
          requestId={state.requestId}
          httpStatus={state.httpStatus}
          operation="portfolio_review.list"
          onRetry={retry}
        />
      ) : reviews?.length === 0 ? (
        <EmptyState title={t("emptyTitle")} message={t("emptyMessage")} />
      ) : reviews ? (
        <ol className="card-list" aria-label={t("ariaLabel")} aria-busy={refreshPending}>
          {reviews.map((review, index) => (
            <ReviewCard
              key={`${review.review_id}-${index}`}
              review={review}
            />
          ))}
        </ol>
      ) : null}
    </div>
  );
}
