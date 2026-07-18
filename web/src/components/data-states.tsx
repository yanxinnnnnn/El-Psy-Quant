import Link from "next/link";
import { useTranslations } from "next-intl";

import { useErrorPresentation } from "@/i18n/errors";

export function RequestId({ value }: { value: string | null }) {
  const t = useTranslations("common");
  return value ? <p className="request-id">{t("requestId", { requestId: value })}</p> : null;
}

export function LoadingState({ message }: { message: string }) {
  const t = useTranslations("common");
  return (
    <section className="state-panel state-panel--loading" role="status" aria-live="polite" aria-busy="true">
      <p className="eyebrow">{t("states.loading")}</p>
      <h2>{t("loading.title")}</h2>
      <p>{message}</p>
    </section>
  );
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  const t = useTranslations("common");
  return (
    <section className="state-panel state-panel--empty">
      <p className="eyebrow">{t("states.empty")}</p>
      <h2>{title}</h2>
      <p>{message}</p>
    </section>
  );
}

export function TechnicalAuditDetails({
  operation,
  httpStatus,
  entityLabel,
  entityId,
  code,
  requestId,
  message,
}: {
  operation?: string;
  httpStatus?: number | null;
  entityLabel?: string;
  entityId?: string;
  code?: string | null;
  requestId?: string | null;
  message?: string | null;
}) {
  const t = useTranslations("errors.technical");
  const common = useTranslations("common");
  const hasFields = Boolean(
    operation
    || httpStatus
    || (entityLabel && entityId)
    || code
    || requestId
    || message,
  );
  if (!hasFields) return null;
  return (
    <section className="technical-audit-details" aria-label={t("title")}>
      <h3>{t("title")}</h3>
      <dl className="technical-audit-grid">
        {operation ? <div><dt>{t("operation")}</dt><dd><code className="raw-value">{operation}</code></dd></div> : null}
        {httpStatus ? <div><dt>{t("httpStatus")}</dt><dd>{httpStatus}</dd></div> : null}
        {entityLabel && entityId ? <div><dt>{t("entity")}</dt><dd><span>{entityLabel}: </span><code className="raw-value">{entityId}</code></dd></div> : null}
        {code ? <div><dt>{t("errorCode")}</dt><dd><code className="raw-value">{common("errorCode", { code })}</code></dd></div> : null}
        {requestId ? <div><dt>{t("requestId")}</dt><dd><code className="raw-value">{common("requestId", { requestId })}</code></dd></div> : null}
      </dl>
      {message ? (
        <details className="audit-disclosure" open>
          <summary>{common("backendDetail")}</summary>
          <p><span className="visually-hidden">{t("backendMessage")}: </span>{message}</p>
        </details>
      ) : null}
    </section>
  );
}

export function ErrorState({
  title,
  message,
  code,
  requestId,
  onRetry,
  retryLabel,
  className,
  backHref,
  backLabel,
  operation,
  httpStatus,
  entityLabel,
  entityId,
}: {
  title: string;
  message?: string | null;
  code?: string | null;
  requestId: string | null;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
  backHref?: string;
  backLabel?: string;
  operation?: string;
  httpStatus?: number | null;
  entityLabel?: string;
  entityId?: string;
}) {
  const common = useTranslations("common");
  const presentation = useErrorPresentation(code);
  const resolvedTitle = presentation.useContextTitle ? title : presentation.title;
  return (
    <section className={`state-panel state-panel--error${className ? ` ${className}` : ""}`} role="alert">
      <p className="eyebrow">{presentation.stateLabel}</p>
      <h2>{resolvedTitle}</h2>
      <p>{presentation.explanation}</p>
      <p>{presentation.recovery}</p>
      <TechnicalAuditDetails
        operation={operation}
        httpStatus={httpStatus}
        entityLabel={entityLabel}
        entityId={entityId}
        code={code}
        requestId={requestId}
        message={message}
      />
      <div className="state-panel__actions">
        {onRetry ? (
          <button className="secondary-button" type="button" onClick={onRetry}>
            {retryLabel ?? common("actions.retry")}
          </button>
        ) : null}
        {backHref && backLabel ? (
          <Link className="text-link" href={backHref}>
            {backLabel}
          </Link>
        ) : null}
      </div>
    </section>
  );
}
