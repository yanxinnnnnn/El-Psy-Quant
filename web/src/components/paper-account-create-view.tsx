"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ErrorState, RequestId } from "@/components/data-states";
import {
  PaperAccountLifecycleValue,
  PaperAccountProjectionStatusValue,
} from "@/components/domain-values";
import {
  ApiClientError,
  createPaperAccount,
  type PaperAccountCommandResponse,
} from "@/lib/api-client";
import {
  isCanonicalPaperDecimal,
  isNormalizedPaperText,
} from "@/lib/paper-accounts";

type Failure = {
  code: string;
  message: string;
  requestId: string | null;
  httpStatus: number;
} | null;

export function PaperAccountCreateView() {
  const t = useTranslations("paperAccounts.create");
  const common = useTranslations("paperAccounts.common");
  const validation = useTranslations("paperAccounts.validation");
  const [displayName, setDisplayName] = useState("");
  const [baseCurrency, setBaseCurrency] = useState("");
  const [initialCash, setInitialCash] = useState("");
  const [actor, setActor] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [failure, setFailure] = useState<Failure>(null);
  const [result, setResult] = useState<PaperAccountCommandResponse | null>(null);

  return (
    <div className="business-workspace">
      <header className="page-heading">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
        <Link className="text-link" href="/paper-accounts">{t("back")}</Link>
      </header>

      <aside className="boundary-note" aria-label={common("authorityTitle")}>
        <strong>{common("authorityTitle")}</strong>
        <p>{t("authority")}</p>
      </aside>

      {validationMessage ? (
        <section className="state-panel state-panel--error" role="alert">
          <h2>{validation("title")}</h2>
          <p>{validationMessage}</p>
          <p>{validation("noRequest")}</p>
        </section>
      ) : null}
      {failure ? (
        <ErrorState
          title={t("failureTitle")}
          code={failure.code}
          message={failure.message}
          requestId={failure.requestId}
          httpStatus={failure.httpStatus}
          operation="paper_account.create"
        />
      ) : null}
      {result ? (
        <section className="state-panel state-panel--success" role="status">
          <p className="eyebrow">{result.replayed ? t("replayed") : t("created")}</p>
          <h2>{result.replayed ? t("replayedTitle") : t("createdTitle")}</h2>
          <RequestId value={result.request_id} />
          <dl className="compact-definitions">
            <div>
              <dt>{common("accountId")}</dt>
              <dd><code className="raw-value">{result.account.account_id}</code></dd>
            </div>
            <div>
              <dt>{common("lifecycleStatus")}</dt>
              <dd>
                <PaperAccountLifecycleValue value={result.account.lifecycle_status} />
              </dd>
            </div>
            <div>
              <dt>{common("projectionStatus")}</dt>
              <dd>
                <PaperAccountProjectionStatusValue
                  value={result.account.projection_status}
                />
              </dd>
            </div>
          </dl>
          <Link
            className="primary-link"
            href={`/paper-accounts/${encodeURIComponent(result.account.account_id)}`}
          >
            {t("inspect")}
          </Link>
        </section>
      ) : null}

      <form
        className="business-form paper-account-form"
        onSubmit={async (event) => {
          event.preventDefault();
          setValidationMessage(null);
          setFailure(null);
          setResult(null);
          const message =
            !isNormalizedPaperText(displayName, 200)
              ? validation("displayName")
              : !/^[A-Za-z]{3}$/.test(baseCurrency)
                ? validation("baseCurrency")
                : !isCanonicalPaperDecimal(initialCash)
                  ? validation("decimal")
                  : !isNormalizedPaperText(actor, 512)
                    ? validation("actor")
                    : !isNormalizedPaperText(idempotencyKey, 128)
                      ? validation("idempotencyKey")
                      : !confirmed
                        ? validation("confirmation")
                        : null;
          if (message !== null) {
            setValidationMessage(message);
            return;
          }
          setSubmitting(true);
          try {
            const response = await createPaperAccount(
              {
                display_name: displayName,
                base_currency: baseCurrency,
                initial_cash: initialCash,
                actor,
              },
              idempotencyKey,
            );
            setResult(response.data);
          } catch (error) {
            if (error instanceof ApiClientError) {
              setFailure({
                code: error.code,
                message: error.publicMessage,
                requestId: error.requestId,
                httpStatus: error.status,
              });
            } else {
              setFailure({
                code: "api_request_failed",
                message: t("unexpectedFailure"),
                requestId: null,
                httpStatus: 0,
              });
            }
          } finally {
            setSubmitting(false);
          }
        }}
      >
        <fieldset>
          <legend>{t("identityLegend")}</legend>
          <div className="form-grid">
            <label>
              {t("displayName")}
              <input
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                maxLength={200}
                required
              />
            </label>
            <label>
              {t("baseCurrency")}
              <input
                value={baseCurrency}
                onChange={(event) => setBaseCurrency(event.target.value)}
                maxLength={3}
                required
              />
            </label>
            <label>
              {t("initialCash")}
              <input
                value={initialCash}
                onChange={(event) => setInitialCash(event.target.value)}
                inputMode="decimal"
                required
              />
              <span className="field-help">{t("decimalHelp")}</span>
            </label>
            <label>
              {t("actor")}
              <input
                value={actor}
                onChange={(event) => setActor(event.target.value)}
                maxLength={512}
                required
              />
            </label>
            <label>
              {t("idempotencyKey")}
              <input
                value={idempotencyKey}
                onChange={(event) => setIdempotencyKey(event.target.value)}
                maxLength={128}
                required
              />
            </label>
          </div>
        </fieldset>
        <label className="confirmation-control">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(event) => setConfirmed(event.target.checked)}
          />
          <span>{t("confirmation")}</span>
        </label>
        <button className="primary-button" type="submit" disabled={submitting}>
          {submitting ? t("submitting") : t("submit")}
        </button>
      </form>
    </div>
  );
}
