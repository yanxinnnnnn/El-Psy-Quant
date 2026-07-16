import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const HEALTH_ONLY = process.argv.includes("--health-only");
const DEFAULT_ORIGIN = "http://127.0.0.1:3000";
const ENVIRONMENT_KEYS = new Set([
  "EL_PSY_QUANT_FOUNDER_USERNAME",
  "EL_PSY_QUANT_FOUNDER_PASSWORD",
  "EL_PSY_QUANT_MVP_ORIGIN",
]);

function loadRootEnvironment() {
  const path = fileURLToPath(new URL("../../.env", import.meta.url));
  if (!existsSync(path)) {
    return;
  }
  for (const sourceLine of readFileSync(path, "utf8").split(/\r?\n/u)) {
    const line = sourceLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }
    const separator = line.indexOf("=");
    if (separator <= 0) {
      continue;
    }
    const key = line.slice(0, separator).trim();
    if (!ENVIRONMENT_KEYS.has(key) || process.env[key] !== undefined) {
      continue;
    }
    let value = line.slice(separator + 1).trim();
    if (
      value.length >= 2 &&
      ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'")))
    ) {
      value = value.slice(1, -1);
    }
    process.env[key] = value;
  }
}

function requireSetting(name) {
  const value = process.env[name];
  if (value === undefined || value.length === 0) {
    throw new Error(`${name} is required for authenticated MVP verification`);
  }
  return value;
}

function basicAuthorization(username, password) {
  return `Basic ${Buffer.from(`${username}:${password}`, "ascii").toString("base64")}`;
}

async function request(origin, path, { authorization, body } = {}) {
  const headers = { Accept: "application/json" };
  if (authorization !== undefined) {
    headers.Authorization = authorization;
  }
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  return fetch(`${origin}${path}`, {
    method: body === undefined ? "GET" : "POST",
    cache: "no-store",
    headers,
    redirect: "manual",
    signal: AbortSignal.timeout(10_000),
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
}

async function expectStatus(response, expected, label) {
  if (response.status !== expected) {
    const detail = (await response.text()).slice(0, 240);
    throw new Error(
      `${label} returned HTTP ${response.status}; expected ${expected}: ${detail}`,
    );
  }
}

async function expectJson(response, label) {
  try {
    return await response.json();
  } catch {
    throw new Error(`${label} did not return JSON`);
  }
}

function lifecycleProposal() {
  return {
    proposal_id: "mvp-smoke-proposal",
    source_snapshot: {
      snapshot_id: "mvp-smoke-research-snapshot",
      strategy_id: "moving_average_crossover",
      lifecycle_state: "research_review",
      rationale: "Verify the existing stateless lifecycle boundary.",
      declared_by: "founder",
      declared_timestamp: "2026-07-15T00:00:00Z",
      notes: [],
      warnings: [],
    },
    target_state: "paper_review",
    rationale: "Verify proposal normalization through the same-origin gateway.",
    evidence_references: [
      {
        reference_type: "strategy_decision_record",
        reference_id: "mvp-smoke-decision",
        label: "Verification evidence",
        description: null,
      },
      {
        reference_type: "promotion_record",
        reference_id: "mvp-smoke-promotion",
        label: null,
        description: "Verification evidence",
      },
    ],
    requested_by: "founder",
    requested_timestamp: "2026-07-15T00:01:00Z",
    notes: [],
    warnings: [],
  };
}

async function verifyAuthenticationAndHealth(origin, authorization) {
  const unauthenticated = await request(
    origin,
    "/api/backend/api/v1/health",
  );
  await expectStatus(unauthenticated, 401, "Unauthenticated gateway health");
  if (!unauthenticated.headers.get("www-authenticate")?.startsWith("Basic ")) {
    throw new Error("Unauthenticated gateway health did not return a Basic challenge");
  }

  const health = await request(origin, "/api/backend/api/v1/health", {
    authorization,
  });
  await expectStatus(health, 200, "Authenticated gateway health");
  const payload = await expectJson(health, "Authenticated gateway health");
  const expected = {
    status: "ok",
    service: "el-psy-quant",
    api_version: "v1",
  };
  if (JSON.stringify(payload) !== JSON.stringify(expected)) {
    throw new Error("Authenticated gateway health returned an unexpected contract");
  }
  if (!health.headers.get("x-request-id")) {
    throw new Error("Authenticated gateway health did not return a request ID");
  }
}

async function verifyWorkspaceRoutes(origin, authorization) {
  const routes = [
    "/",
    "/strategies",
    "/research-runs",
    "/evidence-manifests",
    "/paper-jobs",
    "/paper-jobs/new",
    "/portfolio-records",
    "/comparisons",
    "/lifecycle-review",
  ];
  for (const path of routes) {
    const response = await request(origin, path, { authorization });
    await expectStatus(response, 200, `Workspace route ${path}`);
    const contentType = response.headers.get("content-type") ?? "";
    if (!contentType.startsWith("text/html")) {
      throw new Error(`Workspace route ${path} did not return HTML`);
    }
  }
}

async function verifyReadWorkflows(origin, authorization) {
  const reads = [
    ["/api/backend/api/v1/strategies", "strategies"],
    ["/api/backend/api/v1/research-runs", "runs"],
    ["/api/backend/api/v1/evidence-manifests", "manifests"],
    ["/api/backend/api/v1/paper-jobs?limit=20", null],
  ];
  for (const [path, collectionKey] of reads) {
    const response = await request(origin, path, { authorization });
    await expectStatus(response, 200, `Workflow read ${path}`);
    const payload = await expectJson(response, `Workflow read ${path}`);
    const collection = collectionKey === null ? payload : payload[collectionKey];
    if (!Array.isArray(collection)) {
      throw new Error(`Workflow read ${path} returned an unexpected contract`);
    }
  }
}

async function verifyLifecycleCommands(origin, authorization) {
  const proposal = lifecycleProposal();
  const proposalResponse = await request(
    origin,
    "/api/backend/api/v1/lifecycle-transition-proposals",
    { authorization, body: proposal },
  );
  await expectStatus(proposalResponse, 200, "Lifecycle proposal command");
  const proposalPayload = await expectJson(
    proposalResponse,
    "Lifecycle proposal command",
  );
  if (proposalPayload.proposal?.proposal_id !== proposal.proposal_id) {
    throw new Error("Lifecycle proposal command returned an unexpected contract");
  }

  const reviewResponse = await request(
    origin,
    "/api/backend/api/v1/lifecycle-transition-records",
    {
      authorization,
      body: {
        transition_record_id: "mvp-smoke-review",
        proposal,
        review_outcome: "deferred",
        rationale: "Verify explicit human review without applying a transition.",
        resulting_snapshot: null,
        reviewed_by: "founder",
        reviewed_timestamp: "2026-07-15T00:02:00Z",
        notes: [],
        warnings: [],
      },
    },
  );
  await expectStatus(reviewResponse, 200, "Lifecycle human-review command");
  const reviewPayload = await expectJson(
    reviewResponse,
    "Lifecycle human-review command",
  );
  if (
    reviewPayload.transition_record?.transition_record_id !== "mvp-smoke-review" ||
    reviewPayload.transition_record?.resulting_snapshot !== null
  ) {
    throw new Error("Lifecycle human-review command returned an unexpected contract");
  }
}

async function main() {
  loadRootEnvironment();
  const username = requireSetting("EL_PSY_QUANT_FOUNDER_USERNAME");
  const password = requireSetting("EL_PSY_QUANT_FOUNDER_PASSWORD");
  const origin = process.env.EL_PSY_QUANT_MVP_ORIGIN ?? DEFAULT_ORIGIN;
  const parsedOrigin = new URL(origin);
  if (
    !["127.0.0.1", "localhost", "[::1]"].includes(parsedOrigin.hostname) ||
    parsedOrigin.pathname !== "/" ||
    parsedOrigin.search ||
    parsedOrigin.hash
  ) {
    throw new Error("EL_PSY_QUANT_MVP_ORIGIN must be a complete loopback origin");
  }
  const authorization = basicAuthorization(username, password);

  await verifyAuthenticationAndHealth(parsedOrigin.origin, authorization);
  if (HEALTH_ONLY) {
    return;
  }
  await verifyWorkspaceRoutes(parsedOrigin.origin, authorization);
  await verifyReadWorkflows(parsedOrigin.origin, authorization);
  await verifyLifecycleCommands(parsedOrigin.origin, authorization);
  console.log(
    "MVP verification passed: auth, same-origin health, workspace routes, read workflows, and stateless lifecycle commands.",
  );
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : "Unknown verification failure";
  console.error(`MVP verification failed: ${message}`);
  process.exitCode = 1;
});
