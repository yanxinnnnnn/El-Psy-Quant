"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiClientError, fetchHealth } from "@/lib/api-client";

type HealthState =
  | { status: "loading" }
  | { status: "available"; requestId: string | null }
  | { status: "unavailable"; message: string; requestId: string | null };

export function HealthPanel() {
  const [health, setHealth] = useState<HealthState>({ status: "loading" });
  const requestSequence = useRef(0);

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
          message: error.publicMessage,
          requestId: error.requestId,
        });
      } else {
        setHealth({
          status: "unavailable",
          message: "The local API is unavailable.",
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
            message: error.publicMessage,
            requestId: error.requestId,
          });
        } else {
          setHealth({
            status: "unavailable",
            message: "The local API is unavailable.",
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
          <p className="eyebrow">Local dependency</p>
          <h2 id="api-connectivity-title">API connectivity</h2>
        </div>
        <span className={`status-badge status-badge--${health.status}`} aria-live="polite">
          <span aria-hidden="true" className="status-badge__dot" />
          {health.status === "loading"
            ? "Checking"
            : health.status === "available"
              ? "Available"
              : "Unavailable"}
        </span>
      </div>

      {health.status === "loading" ? (
        <p className="health-panel__message" role="status">
          Checking the FastAPI process through the same-origin gateway…
        </p>
      ) : health.status === "available" ? (
        <div className="health-panel__message" role="status">
          <p>The local API process is responding on the versioned health endpoint.</p>
          {health.requestId ? <p className="request-id">Request {health.requestId}</p> : null}
        </div>
      ) : (
        <div className="health-panel__message" role="alert">
          <p>{health.message} Start FastAPI on loopback, then retry.</p>
          {health.requestId ? <p className="request-id">Request {health.requestId}</p> : null}
        </div>
      )}

      <button
        className="retry-button"
        type="button"
        onClick={() => void checkHealth()}
        disabled={health.status === "loading"}
      >
        {health.status === "loading" ? "Checking…" : "Retry connection"}
      </button>
    </section>
  );
}
