// @vitest-environment node

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function source(path: string) {
  return readFileSync(resolve(process.cwd(), path), "utf8");
}

describe("Sprint 204 Web authority boundary", () => {
  it("uses generated contracts as the M33 transport type source", () => {
    const client = source("src/lib/api-client.ts");
    const validators = source("src/lib/strategy-order-validators.ts");
    expect(client).toContain('import type { paths } from "@/generated/api-types"');
    expect(client).toContain("type StrategySignalEvaluateRequest = PostRequestBody");
    expect(client).toContain("type PreTradeRiskDecisionCreateRequest = PostRequestBody");
    expect(validators).toContain('import type { components } from "@/generated/api-types"');
    expect(validators).not.toMatch(/\bany\b/);
  });

  it("introduces no parallel browser authority or mutation client", () => {
    const workspace = source("src/components/strategy-to-risk-workspace.tsx");
    expect(workspace).not.toMatch(/\bfetch\s*\(/);
    expect(workspace).not.toMatch(/postPaperAccount|createPaperAccount|runMarket|advanceReplay|pauseReplay|resumeReplay/);
    expect(workspace).not.toMatch(/sqlite|python process|qmt|miniqmt|broker adapter/i);
    expect(workspace).not.toMatch(/\bany\b/);
  });

  it("keeps account identity out of the dedicated Risk request block", () => {
    const workspace = source("src/components/strategy-to-risk-workspace.tsx");
    const riskBlock = workspace.slice(
      workspace.indexOf("const riskRequest"),
      workspace.indexOf("const riskFingerprint"),
    );
    const accountBlock = riskBlock.slice(
      riskBlock.indexOf("account: {"),
      riskBlock.indexOf("market: {"),
    );
    expect(accountBlock).toContain("expected_account_head_version");
    expect(accountBlock).toContain("expected_account_head_event_id");
    expect(accountBlock).toContain("expected_account_head_chain_digest");
    expect(accountBlock).not.toContain("account_id");
  });
});
