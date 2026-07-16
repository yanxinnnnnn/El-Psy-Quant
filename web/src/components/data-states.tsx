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
    <section className="state-panel" role="status" aria-busy="true">
      <p className="eyebrow">{t("states.loading")}</p>
      <h2>{t("loading.title")}</h2>
      <p>{message}</p>
    </section>
  );
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  const t = useTranslations("common");
  return (
    <section className="state-panel">
      <p className="eyebrow">{t("states.empty")}</p>
      <h2>{title}</h2>
      <p>{message}</p>
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
}) {
  const t = useTranslations("common");
  const presentation = useErrorPresentation(code);
  const resolvedTitle = presentation.useContextTitle ? title : presentation.title;
  return (
    <section className={`state-panel state-panel--error${className ? ` ${className}` : ""}`} role="alert">
      <p className="eyebrow">{t("states.unavailable")}</p>
      <h2>{resolvedTitle}</h2>
      <p>{presentation.explanation}</p>
      <p>{presentation.recovery}</p>
      {code ? <p className="request-id">{t("errorCode", { code })}</p> : null}
      {message ? (
        <details>
          <summary>{t("backendDetail")}</summary>
          <p>{message}</p>
        </details>
      ) : null}
      <RequestId value={requestId} />
      <div className="state-panel__actions">
        {onRetry ? (
          <button className="retry-button" type="button" onClick={onRetry}>
            {retryLabel ?? t("actions.retry")}
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
