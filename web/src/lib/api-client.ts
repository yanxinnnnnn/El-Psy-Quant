import type { paths } from "@/generated/api-types";

const API_BASE_PATH = "/api/backend";
const HEALTH_PATH = "/api/v1/health";
const REQUEST_ID_HEADER = "X-Request-ID";
const MAX_CODE_LENGTH = 80;
const MAX_MESSAGE_LENGTH = 240;
const MAX_REQUEST_ID_LENGTH = 128;

type HealthOperation = paths[typeof HEALTH_PATH]["get"];
export type HealthResponse =
  HealthOperation["responses"][200]["content"]["application/json"];

type PublicErrorEnvelope = {
  error: {
    code: string;
    message: string;
  };
  request_id: string;
};

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly publicMessage: string;
  readonly requestId: string | null;

  constructor({
    status,
    code,
    publicMessage,
    requestId,
  }: {
    status: number;
    code: string;
    publicMessage: string;
    requestId: string | null;
  }) {
    super(publicMessage);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.publicMessage = publicMessage;
    this.requestId = requestId;
  }
}

function boundedString(value: unknown, maximumLength: number): string | null {
  return typeof value === "string" && value.length > 0 && value.length <= maximumLength
    ? value
    : null;
}

function requestIdFrom(response: Response, bodyRequestId?: unknown): string | null {
  return (
    boundedString(response.headers.get(REQUEST_ID_HEADER), MAX_REQUEST_ID_LENGTH) ??
    boundedString(bodyRequestId, MAX_REQUEST_ID_LENGTH)
  );
}

function isHealthResponse(value: unknown): value is HealthResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    candidate.status === "ok" &&
    candidate.service === "el-psy-quant" &&
    candidate.api_version === "v1"
  );
}

function publicErrorEnvelope(value: unknown): PublicErrorEnvelope | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  const candidate = value as Record<string, unknown>;
  if (typeof candidate.error !== "object" || candidate.error === null) {
    return null;
  }
  const detail = candidate.error as Record<string, unknown>;
  const code = boundedString(detail.code, MAX_CODE_LENGTH);
  const message = boundedString(detail.message, MAX_MESSAGE_LENGTH);
  const requestId = boundedString(candidate.request_id, MAX_REQUEST_ID_LENGTH);
  if (code === null || message === null || requestId === null) {
    return null;
  }
  return { error: { code, message }, request_id: requestId };
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function fetchHealth(
  fetchImplementation: typeof fetch = fetch,
): Promise<{ data: HealthResponse; requestId: string | null }> {
  let response: Response;
  try {
    response = await fetchImplementation(`${API_BASE_PATH}${HEALTH_PATH}`, {
      method: "GET",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  } catch {
    throw new ApiClientError({
      status: 0,
      code: "api_unavailable",
      publicMessage: "The local API is unavailable.",
      requestId: null,
    });
  }

  const body = await safeJson(response);
  const requestId = requestIdFrom(response);
  if (!response.ok) {
    const envelope = publicErrorEnvelope(body);
    if (envelope !== null) {
      throw new ApiClientError({
        status: response.status,
        code: envelope.error.code,
        publicMessage: envelope.error.message,
        requestId: requestIdFrom(response, envelope.request_id),
      });
    }
    throw new ApiClientError({
      status: response.status,
      code: "api_request_failed",
      publicMessage: "The local API request failed.",
      requestId,
    });
  }

  if (!isHealthResponse(body)) {
    throw new ApiClientError({
      status: response.status,
      code: "api_response_invalid",
      publicMessage: "The local API returned an invalid response.",
      requestId,
    });
  }

  return { data: body, requestId };
}
