import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_ORIGIN = "http://127.0.0.1:3000";
const LOCALE_COOKIE_NAME = "el_psy_quant_locale";
const SUPPORTED_MODES = new Set(["standard", "demo"]);
const ENVIRONMENT_KEYS = new Set([
  "EL_PSY_QUANT_FOUNDER_USERNAME",
  "EL_PSY_QUANT_FOUNDER_PASSWORD",
  "EL_PSY_QUANT_MVP_ORIGIN",
  "EL_PSY_QUANT_WORKSPACE_MODE",
]);

export const TOP_LEVEL_ROUTES = Object.freeze([
  "/",
  "/strategies",
  "/research-runs",
  "/evidence-manifests",
  "/paper-jobs",
  "/paper-jobs/new",
  "/portfolio-records",
  "/comparisons",
  "/lifecycle-review",
]);

export const FORBIDDEN_MUTATION_FRAGMENTS = Object.freeze([
  "/api/backend/api/v1/paper-jobs/",
  "/api/backend/api/v1/lifecycle-transition-proposals",
  "/api/backend/api/v1/lifecycle-transition-records",
]);

function loadRootEnvironment(environment = process.env) {
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
    if (!ENVIRONMENT_KEYS.has(key) || environment[key] !== undefined) {
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
    environment[key] = value;
  }
}

function requireSetting(environment, name) {
  const value = environment[name];
  if (value === undefined || value.length === 0) {
    throw new Error(`${name} is required for authenticated MVP verification`);
  }
  return value;
}

export function basicAuthorization(username, password) {
  return `Basic ${Buffer.from(`${username}:${password}`, "ascii").toString("base64")}`;
}

export function buildRequestOptions({
  authorization,
  body,
  cookie,
  accept = "application/json",
} = {}) {
  const headers = { Accept: accept };
  if (authorization !== undefined) {
    headers.Authorization = authorization;
  }
  if (cookie !== undefined) {
    headers.Cookie = cookie;
  }
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  return {
    method: body === undefined ? "GET" : "POST",
    cache: "no-store",
    headers,
    redirect: "manual",
    signal: AbortSignal.timeout(10_000),
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  };
}

export async function request(
  fetchImpl,
  origin,
  path,
  options = {},
) {
  return fetchImpl(
    `${origin}${path}`,
    buildRequestOptions(options),
  );
}

export async function expectStatus(response, expected, label) {
  if (response.status !== expected) {
    throw new Error(
      `${label} returned HTTP ${response.status}; expected ${expected}`,
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

function requireRequestId(response, label) {
  if (!response.headers.get("x-request-id")) {
    throw new Error(`${label} did not return a request ID`);
  }
}

function cookieFromResponse(response, expectedLocale) {
  const setCookie = response.headers.get("set-cookie") ?? "";
  const expected = `${LOCALE_COOKIE_NAME}=${expectedLocale}`;
  if (!setCookie.startsWith(expected)) {
    throw new Error(`Locale switch to ${expectedLocale} did not set the expected cookie`);
  }
  return expected;
}

async function verifyAuthenticationAndHealth(fetchImpl, origin, authorization) {
  const unauthenticated = await request(
    fetchImpl,
    origin,
    "/api/backend/api/v1/health",
  );
  await expectStatus(unauthenticated, 401, "Unauthenticated gateway health");
  if (!unauthenticated.headers.get("www-authenticate")?.startsWith("Basic ")) {
    throw new Error("Unauthenticated gateway health did not return a Basic challenge");
  }
  requireRequestId(unauthenticated, "Unauthenticated gateway health");

  const health = await request(
    fetchImpl,
    origin,
    "/api/backend/api/v1/health",
    { authorization },
  );
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
  requireRequestId(health, "Authenticated gateway health");
}

async function setLocale(fetchImpl, origin, authorization, locale) {
  const response = await request(fetchImpl, origin, "/api/locale", {
    authorization,
    body: { locale },
  });
  await expectStatus(response, 200, `Locale switch to ${locale}`);
  const payload = await expectJson(response, `Locale switch to ${locale}`);
  if (payload.locale !== locale) {
    throw new Error(`Locale switch to ${locale} returned an unexpected contract`);
  }
  return cookieFromResponse(response, locale);
}

async function verifyLocalizedDocument(
  fetchImpl,
  origin,
  authorization,
  locale,
  cookie,
) {
  const response = await request(fetchImpl, origin, "/", {
    authorization,
    cookie,
    accept: "text/html",
  });
  await expectStatus(response, 200, `${locale} workspace document`);
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.startsWith("text/html")) {
    throw new Error(`${locale} workspace document did not return HTML`);
  }
  const html = await response.text();
  if (!html.includes(`<html lang="${locale}">`)) {
    throw new Error(`${locale} workspace document did not preserve document language`);
  }
  const representativeCopy = locale === "en"
    ? "Founder Workspace"
    : "创始人工作台";
  if (!html.includes(representativeCopy)) {
    throw new Error(`${locale} workspace document omitted representative localized copy`);
  }
}

async function verifyLocaleSwitching(fetchImpl, origin, authorization) {
  const chineseCookie = await setLocale(
    fetchImpl,
    origin,
    authorization,
    "zh-CN",
  );
  await verifyLocalizedDocument(
    fetchImpl,
    origin,
    authorization,
    "zh-CN",
    chineseCookie,
  );
  const englishCookie = await setLocale(
    fetchImpl,
    origin,
    authorization,
    "en",
  );
  await verifyLocalizedDocument(
    fetchImpl,
    origin,
    authorization,
    "en",
    englishCookie,
  );
  return { chineseCookie, englishCookie };
}

async function verifyWorkspaceRoutes(
  fetchImpl,
  origin,
  authorization,
  cookies,
) {
  const detailRoutes = ["/strategies/moving_average_crossover"];
  for (const [locale, cookie] of [
    ["en", cookies.englishCookie],
    ["zh-CN", cookies.chineseCookie],
  ]) {
    for (const path of [...TOP_LEVEL_ROUTES, ...detailRoutes]) {
      const response = await request(fetchImpl, origin, path, {
        authorization,
        cookie,
        accept: "text/html",
      });
      await expectStatus(response, 200, `${locale} workspace route ${path}`);
      if (!(response.headers.get("content-type") ?? "").startsWith("text/html")) {
        throw new Error(`${locale} workspace route ${path} did not return HTML`);
      }
    }
  }
}

async function verifyReadWorkflows(fetchImpl, origin, authorization) {
  const reads = [
    ["/api/backend/api/v1/strategies", "strategies"],
    ["/api/backend/api/v1/research-runs", "runs"],
    ["/api/backend/api/v1/evidence-manifests", "manifests"],
    ["/api/backend/api/v1/paper-jobs?limit=20", null],
  ];
  for (const [path, collectionKey] of reads) {
    const response = await request(fetchImpl, origin, path, { authorization });
    await expectStatus(response, 200, `Workflow read ${path}`);
    const payload = await expectJson(response, `Workflow read ${path}`);
    const collection = collectionKey === null ? payload : payload[collectionKey];
    if (!Array.isArray(collection)) {
      throw new Error(`Workflow read ${path} returned an unexpected contract`);
    }
  }
}

function stableDescriptorIdentity(descriptor) {
  return {
    dataset_id: descriptor.dataset_id,
    dataset_version: descriptor.dataset_version,
    canonical_strategy_name: descriptor.canonical_strategy_name,
    research_run: descriptor.research_run,
    evidence_manifests: descriptor.evidence_manifests,
    paper_jobs: descriptor.paper_jobs?.map(({ job_id, run_id }) => ({
      job_id,
      run_id,
    })),
    comparison_candidate_job_ids: descriptor.comparison_candidate_job_ids,
  };
}

async function readDemoDescriptor(
  fetchImpl,
  origin,
  authorization,
  cookie,
) {
  const response = await request(
    fetchImpl,
    origin,
    "/api/backend/api/v1/demo-workspace",
    { authorization, cookie },
  );
  await expectStatus(response, 200, "Demo workspace descriptor");
  return expectJson(response, "Demo workspace descriptor");
}

async function verifyDemoJourney(
  fetchImpl,
  origin,
  authorization,
  cookies,
) {
  const descriptor = await readDemoDescriptor(
    fetchImpl,
    origin,
    authorization,
    cookies.englishCookie,
  );
  const localizedDescriptor = await readDemoDescriptor(
    fetchImpl,
    origin,
    authorization,
    cookies.chineseCookie,
  );
  if (
    descriptor.schema_version !== 1 ||
    typeof descriptor.canonical_strategy_name !== "string" ||
    !Array.isArray(descriptor.evidence_manifests) ||
    !Array.isArray(descriptor.paper_jobs) ||
    descriptor.paper_jobs.length < 2 ||
    !Array.isArray(descriptor.comparison_candidate_job_ids) ||
    descriptor.comparison_candidate_job_ids.length < 2 ||
    new Set(descriptor.comparison_candidate_job_ids).size !==
      descriptor.comparison_candidate_job_ids.length
  ) {
    throw new Error("Demo workspace descriptor returned an unexpected contract");
  }
  if (
    JSON.stringify(stableDescriptorIdentity(descriptor)) !==
    JSON.stringify(stableDescriptorIdentity(localizedDescriptor))
  ) {
    throw new Error("Demo raw identity changed with locale");
  }

  const encoded = encodeURIComponent;
  const exactReads = [
    [
      `/api/backend/api/v1/strategies/${encoded(descriptor.canonical_strategy_name)}`,
      "Demo strategy",
    ],
    [
      `/api/backend/api/v1/research-runs/${encoded(descriptor.research_run.experiment_slug)}/${encoded(descriptor.research_run.run_id)}`,
      "Demo research run",
    ],
    ...descriptor.evidence_manifests.map((reference) => [
      `/api/backend/api/v1/evidence-manifests/${encoded(reference.manifest_type)}/${encoded(reference.artifact_key)}`,
      `Demo evidence ${reference.manifest_type}/${reference.artifact_key}`,
    ]),
  ];
  for (const [path, label] of exactReads) {
    const response = await request(fetchImpl, origin, path, { authorization });
    await expectStatus(response, 200, label);
    await expectJson(response, label);
  }
  for (const job of descriptor.paper_jobs) {
    const jobResponse = await request(
      fetchImpl,
      origin,
      `/api/backend/api/v1/paper-jobs/${encoded(job.job_id)}`,
      { authorization },
    );
    await expectStatus(jobResponse, 200, `Demo paper job ${job.job_id}`);
    const jobPayload = await expectJson(jobResponse, `Demo paper job ${job.job_id}`);
    if (jobPayload.status !== "succeeded" || jobPayload.result_available !== true) {
      throw new Error(`Demo paper job ${job.job_id} is not a succeeded available result`);
    }
    const resultResponse = await request(
      fetchImpl,
      origin,
      `/api/backend/api/v1/paper-jobs/${encoded(job.job_id)}/result`,
      { authorization },
    );
    await expectStatus(resultResponse, 200, `Demo paper result ${job.job_id}`);
    await expectJson(resultResponse, `Demo paper result ${job.job_id}`);
  }
  const comparisonQuery = new URLSearchParams();
  for (const jobId of descriptor.comparison_candidate_job_ids) {
    comparisonQuery.append("job_id", jobId);
  }
  const comparisonResponse = await request(
    fetchImpl,
    origin,
    `/comparisons?${comparisonQuery.toString()}`,
    { authorization, cookie: cookies.englishCookie, accept: "text/html" },
  );
  await expectStatus(comparisonResponse, 200, "Descriptor-provided Demo comparison");
}

async function verifyStandardDescriptorDisabled(
  fetchImpl,
  origin,
  authorization,
  cookies,
) {
  const identities = [];
  for (const cookie of [cookies.englishCookie, cookies.chineseCookie]) {
    const response = await request(
      fetchImpl,
      origin,
      "/api/backend/api/v1/demo-workspace",
      { authorization, cookie },
    );
    await expectStatus(response, 404, "Standard workspace Demo descriptor");
    requireRequestId(response, "Standard workspace Demo descriptor");
    const payload = await expectJson(response, "Standard workspace Demo descriptor");
    if (payload.error?.code !== "demo_workspace_not_configured") {
      throw new Error("Standard workspace exposed an unexpected Demo descriptor response");
    }
    identities.push(payload.error.code);
  }
  if (new Set(identities).size !== 1) {
    throw new Error("Standard raw error identity changed with locale");
  }
}

async function verifySanitizedError(fetchImpl, origin, authorization) {
  const response = await request(
    fetchImpl,
    origin,
    "/api/backend/api/v1/paper-jobs?limit=0",
    { authorization },
  );
  await expectStatus(response, 422, "Representative validation failure");
  requireRequestId(response, "Representative validation failure");
  const payload = await expectJson(response, "Representative validation failure");
  if (payload.error?.code !== "request_validation_error") {
    throw new Error("Representative failure omitted its stable error code");
  }
}

export function validateOrigin(value) {
  const parsedOrigin = new URL(value);
  if (
    !["127.0.0.1", "localhost", "[::1]"].includes(parsedOrigin.hostname) ||
    parsedOrigin.pathname !== "/" ||
    parsedOrigin.search ||
    parsedOrigin.hash
  ) {
    throw new Error("EL_PSY_QUANT_MVP_ORIGIN must be a complete loopback origin");
  }
  return parsedOrigin.origin;
}

export async function runVerification({
  environment = process.env,
  fetchImpl = fetch,
  healthOnly = false,
} = {}) {
  const username = requireSetting(
    environment,
    "EL_PSY_QUANT_FOUNDER_USERNAME",
  );
  const password = requireSetting(
    environment,
    "EL_PSY_QUANT_FOUNDER_PASSWORD",
  );
  const origin = validateOrigin(
    environment.EL_PSY_QUANT_MVP_ORIGIN ?? DEFAULT_ORIGIN,
  );
  const authorization = basicAuthorization(username, password);

  await verifyAuthenticationAndHealth(fetchImpl, origin, authorization);
  if (healthOnly) {
    return "health";
  }
  const workspaceMode = environment.EL_PSY_QUANT_WORKSPACE_MODE ?? "standard";
  if (!SUPPORTED_MODES.has(workspaceMode)) {
    throw new Error("EL_PSY_QUANT_WORKSPACE_MODE must be standard or demo");
  }
  const cookies = await verifyLocaleSwitching(fetchImpl, origin, authorization);
  await verifyWorkspaceRoutes(fetchImpl, origin, authorization, cookies);
  await verifyReadWorkflows(fetchImpl, origin, authorization);
  if (workspaceMode === "demo") {
    await verifyDemoJourney(
      fetchImpl,
      origin,
      authorization,
      cookies,
    );
  } else {
    await verifyStandardDescriptorDisabled(
      fetchImpl,
      origin,
      authorization,
      cookies,
    );
  }
  await verifySanitizedError(fetchImpl, origin, authorization);
  return workspaceMode;
}

async function main() {
  loadRootEnvironment();
  const mode = await runVerification({
    healthOnly: process.argv.includes("--health-only"),
  });
  if (mode !== "health") {
    console.log(
      `MVP verification passed: authenticated health, bilingual routes, read-only workflows, ${mode} identity, stable raw values, and sanitized errors.`,
    );
  }
}

const isMain = process.argv[1] !== undefined &&
  fileURLToPath(import.meta.url) === resolve(process.argv[1]);

if (isMain) {
  main().catch((error) => {
    const message = error instanceof Error
      ? error.message
      : "Unknown verification failure";
    console.error(`MVP verification failed: ${message}`);
    process.exitCode = 1;
  });
}
