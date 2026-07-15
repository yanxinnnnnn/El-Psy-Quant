const NUMBER_FORMATTER = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 4,
});

const PERCENT_FORMATTER = new Intl.NumberFormat("en-US", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatNumber(value: number | null): string {
  return value === null ? "Not available" : NUMBER_FORMATTER.format(value);
}

export function formatPercentage(value: number | null): string {
  return value === null ? "Not available" : PERCENT_FORMATTER.format(value);
}

export function formatDefault(value: number | null): string {
  return value === null ? "Not available" : NUMBER_FORMATTER.format(value);
}
