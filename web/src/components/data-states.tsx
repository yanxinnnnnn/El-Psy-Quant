import Link from "next/link";

export function RequestId({ value }: { value: string | null }) {
  return value ? <p className="request-id">Request {value}</p> : null;
}

export function LoadingState({ message }: { message: string }) {
  return (
    <section className="state-panel" role="status" aria-busy="true">
      <p className="eyebrow">Loading</p>
      <h2>Retrieving backend-owned data</h2>
      <p>{message}</p>
    </section>
  );
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <section className="state-panel">
      <p className="eyebrow">No records</p>
      <h2>{title}</h2>
      <p>{message}</p>
    </section>
  );
}

export function ErrorState({
  title,
  message,
  requestId,
  onRetry,
  backHref,
  backLabel,
}: {
  title: string;
  message: string;
  requestId: string | null;
  onRetry?: () => void;
  backHref?: string;
  backLabel?: string;
}) {
  return (
    <section className="state-panel state-panel--error" role="alert">
      <p className="eyebrow">Unavailable</p>
      <h2>{title}</h2>
      <p>{message}</p>
      <RequestId value={requestId} />
      <div className="state-panel__actions">
        {onRetry ? (
          <button className="retry-button" type="button" onClick={onRetry}>
            Retry
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
