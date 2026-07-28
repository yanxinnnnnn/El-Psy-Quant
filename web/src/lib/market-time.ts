import type { ReplayStatus } from "@/lib/api-client";

export const replayStatuses = [
  "ready",
  "running",
  "paused",
  "completed",
] as const satisfies readonly ReplayStatus[];

export function isIsoDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return (
    Number.isFinite(parsed.getTime()) &&
    parsed.toISOString().slice(0, 10) === value
  );
}
