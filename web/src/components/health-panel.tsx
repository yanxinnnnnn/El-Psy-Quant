"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";

import { ErrorState, RequestId } from "@/components/data-states";
import { useErrorPresentation } from "@/i18n/errors";
import { ApiClientError, fetchHealth } from "@/lib/api-client";

type HealthState =
  | { status: "loading" }
  | { status: "available"; requestId: string | null }
  | { status: "unavailable"; code: string | null; message: string | null; requestId: string | null };

export function HealthPanel() {
  const t = useTranslations("overview.health");
  const [health, setHealth] = useState<HealthState>({ status: "loading" });
  const requestSequence = useRef(0);
  const errorPresentation = useErrorPresentation(health.status === "unavailable" ? health.code : null);

  const checkHealth = useCallback(async () => {
    const sequence = ++requestSequence.current;
    setHealth({ status: "loading" });
    try {
      const result = await fetchHealth();
      if (sequence === requestSequence.current) {
        setHealth({ status: "available", requestId: result.requestId });
      }
    } catch (error) {
      if (sequence !== requestSequence.current) {
        return;
      }
      if (error instanceof ApiClientError) {
        setHealth({
          status: "unavailable",
          code: error.code,
          message: error.publicMessage,
          requestId: error.requestId,
        });
      } else {
        setHealth({
          status: "unavailable",
          code: null,
          message: null,
          requestId: null,
        });
      }
    }
  }, []);

  useEffect(() => {
    const sequence = ++requestSequence.current;
    void fetchHealth()
      .then((result) => {
        if (sequence === requestSequence.current) {
          setHealth({ status: "available", requestId: result.requestId });
        }
      })
      .catch((error: unknown) => {
        if (sequence !== requestSequence.current) {
          return;
        }
        if (error instanceof ApiClientError) {
          setHealth({
            status: "unavailable",
            code: error.code,
            message: error.publicMessage,
            requestId: error.requestId,
          });
        } else {
          setHealth({
            status: "unavailable",
            code: null,
            message: null,
            requestId: null,
          });
        }
      });
    return () => {
      requestSequence.current += 1;
    };
  }, []);

  return (
    <section className="health-panel" aria-labelledby="api-connectivity-title">
      <div className="health-panel__heading">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h2 id="api-connectivity-title">{t("title")}</h2>
        </div>
        <span className={`status-badge status-badge--${health.status}`} aria-live="polite">
          <span aria-hidden="true" className="status-badge__dot" />
          {health.status === "loading"
            ? t("checking")
            : health.status === "available"
              ? t("available")
              : t("unavailable")}
        </span>
      </div>

      {health.status === "loading" ? (
        <p className="health-panel__message" role="status">
          {t("checkingMessage")}
        </p>
      ) : health.status === "available" ? (
        <div className="health-panel__message" role="status">
          <p>{t("availableMessage")}</p>
          <RequestId value={health.requestId} />
        </div>
      ) : (
        <ErrorState
          className="health-panel__message"
          code={health.code}
          title={errorPresentation.title}
          message={health.message}
          requestId={health.requestId}
        />
      )}

      <button
        className="secondary-button"
        type="button"
        onClick={() => void checkHealth()}
        disabled={health.status === "loading"}
      >
        {health.status === "loading" ? t("checkingAction") : t("retry")}
      </button>
    </section>
  );
}
