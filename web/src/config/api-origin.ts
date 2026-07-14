export const DEFAULT_API_ORIGIN = "http://127.0.0.1:8000";

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"]);

export function resolveApiOrigin(configuredValue: string | undefined): string {
  const value = configuredValue === undefined ? DEFAULT_API_ORIGIN : configuredValue;

  if (value.length === 0 || value !== value.trim()) {
    throw new Error("EL_PSY_QUANT_API_ORIGIN must be a complete loopback origin");
  }

  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("EL_PSY_QUANT_API_ORIGIN must be a valid URL");
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("EL_PSY_QUANT_API_ORIGIN must use http or https");
  }
  if (!LOOPBACK_HOSTS.has(parsed.hostname)) {
    throw new Error("EL_PSY_QUANT_API_ORIGIN must use a loopback host");
  }
  if (parsed.username || parsed.password) {
    throw new Error("EL_PSY_QUANT_API_ORIGIN must not include credentials");
  }
  if (parsed.pathname !== "/" || parsed.search || parsed.hash) {
    throw new Error("EL_PSY_QUANT_API_ORIGIN must not include a path, query, or fragment");
  }

  return parsed.origin;
}
