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
  backHref,
  backLabel,
}: {
  title: string;
  message: string;
  code?: string;
  requestId: string | null;
  onRetry?: () => void;
  backHref?: string;
  backLabel?: string;
}) {
  const t = useTranslations("common");
  const presentation = useErrorPresentation(code);
  return (
    <section className="state-panel state-panel--error" role="alert">
      <p className="eyebrow">{t("states.unavailable")}</p>
      <h2>{title}</h2>
      <p>{code ? presentation.explanation : message}</p>
      {code && message ? <p>{message}</p> : null}
      {code ? <p>{presentation.recovery}</p> : null}
      {code ? <p className="request-id">{t("errorCode", { code })}</p> : null}
      <RequestId value={requestId} />
      <div className="state-panel__actions">
        {onRetry ? (
          <button className="retry-button" type="button" onClick={onRetry}>
            {t("actions.retry")}
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
