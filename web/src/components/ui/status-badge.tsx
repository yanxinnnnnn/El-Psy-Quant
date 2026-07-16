import type { ReactNode } from "react";

export type StatusTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "unavailable"
  | "demo";

export function StatusBadge({
  label,
  rawValue,
  tone = "neutral",
}: {
  label: ReactNode;
  rawValue?: string;
  tone?: StatusTone;
}) {
  return (
    <span className={`status-badge status-badge--${tone}`}>
      <span aria-hidden="true" className="status-badge__dot" />
      <span className="status-badge__label">{label}</span>
      {rawValue ? <code className="status-badge__raw">{rawValue}</code> : null}
    </span>
  );
}
