export const portfolioRecordLimits = [25, 50, 100, 200] as const;

export function portfolioRecordErrorTitle(code: string, list = false): string {
  const titles: Readonly<Record<string, string>> = {
    product_database_unavailable: "Product database unavailable",
    paper_artifact_root_unavailable: "Paper artifact root unavailable",
    paper_job_not_found: "Paper job not found",
    paper_job_result_unavailable: "Paper job result unavailable",
    paper_job_result_invalid: "Paper job result is invalid",
  };
  return (
    titles[code] ??
    (list ? "Portfolio records unavailable" : "Portfolio record unavailable")
  );
}
