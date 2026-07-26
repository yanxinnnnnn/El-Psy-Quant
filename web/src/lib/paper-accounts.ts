import type {
  PaperAccountLifecycleRequest,
  PaperAccountLifecycleStatus,
} from "@/lib/api-client";

export const paperAccountLifecycleStatuses = [
  "active",
  "frozen",
  "closed",
] as const satisfies readonly PaperAccountLifecycleStatus[];

export const paperAccountLimits = [25, 50, 100, 200] as const;

export const paperCashMovementTypes = [
  "deposit",
  "withdrawal",
  "manual_adjustment",
  "fee",
  "commission",
  "tax",
] as const;

export const paperPositionAdjustmentCategories = [
  "opening_balance",
  "manual_correction",
  "corporate_action",
  "other",
] as const;

export const paperAccountLifecycleActions = [
  "freeze",
  "reactivate",
  "close",
] as const satisfies readonly PaperAccountLifecycleRequest["action"][];

const canonicalDecimalPattern = /^-?(?:0|[1-9]\d*)(?:\.\d*[1-9])?$/;
const normalizedUtcPattern =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]00:00)$/;
const normalizedTextPattern = /^\S(?:[\s\S]*\S)?$/;
const digestPattern = /^[0-9a-f]{64}$/;

export function isCanonicalPaperDecimal(value: string): boolean {
  return canonicalDecimalPattern.test(value);
}

export function isOptionalNormalizedUtc(value: string): boolean {
  return (
    value === "" ||
    (
      normalizedUtcPattern.test(value) &&
      Number.isFinite(Date.parse(value))
    )
  );
}

export function isNormalizedPaperText(
  value: string,
  maximumLength: number,
): boolean {
  return (
    value.length >= 1 &&
    value.length <= maximumLength &&
    normalizedTextPattern.test(value)
  );
}

export function isSha256Digest(value: string): boolean {
  return digestPattern.test(value);
}
