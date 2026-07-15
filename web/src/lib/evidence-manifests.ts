export const evidenceManifestLabels = {
  strategy_decision_manifest: "Strategy decision",
  report_artifact_manifest: "Report artifact",
  strategy_review_workflow_manifest: "Strategy review workflow",
} as const;

export type EvidenceManifestType = keyof typeof evidenceManifestLabels;

export function evidenceManifestLabel(manifestType: EvidenceManifestType): string {
  return evidenceManifestLabels[manifestType];
}

export function evidenceErrorTitle(code: string): string {
  if (code === "evidence_artifact_root_unavailable") {
    return "Evidence root unavailable";
  }
  if (code === "evidence_artifact_invalid") {
    return "Evidence artifacts are invalid";
  }
  if (code === "evidence_manifest_not_found") {
    return "Evidence manifest not found";
  }
  return "Evidence manifests unavailable";
}

export function nullableText(value: string | null): string {
  return value ?? "Not available";
}
