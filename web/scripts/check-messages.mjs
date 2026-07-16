import { readFile, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { createTranslator } from "next-intl";

export const SUPPORTED_LOCALES = Object.freeze(["en", "zh-CN"]);
export const REQUIRED_NAMESPACES = Object.freeze([
  "common",
  "navigation",
  "overview",
  "strategies",
  "research",
  "evidence",
  "paper-jobs",
  "portfolio-records",
  "comparisons",
  "lifecycle",
  "errors",
]);

function catalogError(message) {
  return new Error(`Message catalog validation failed: ${message}`);
}

export function assertNoDuplicateJsonKeys(source, label) {
  let index = 0;
  const skipWhitespace = () => {
    while (/\s/.test(source[index] ?? "")) index += 1;
  };
  const parseString = () => {
    const start = index;
    index += 1;
    while (index < source.length) {
      if (source[index] === "\\") {
        index += 2;
      } else if (source[index] === '"') {
        index += 1;
        return JSON.parse(source.slice(start, index));
      } else {
        index += 1;
      }
    }
    throw catalogError(`${label} contains an unterminated JSON string`);
  };
  const parseValue = (path) => {
    skipWhitespace();
    if (source[index] === "{") {
      parseObject(path);
      return;
    }
    if (source[index] === "[") {
      index += 1;
      let item = 0;
      skipWhitespace();
      while (source[index] !== "]") {
        parseValue(`${path}[${item}]`);
        item += 1;
        skipWhitespace();
        if (source[index] === ",") {
          index += 1;
          skipWhitespace();
        } else {
          break;
        }
      }
      index += 1;
      return;
    }
    if (source[index] === '"') {
      parseString();
      return;
    }
    while (index < source.length && !/[\s,}\]]/.test(source[index])) index += 1;
  };
  const parseObject = (path) => {
    index += 1;
    const keys = new Set();
    skipWhitespace();
    while (source[index] !== "}") {
      if (source[index] !== '"') {
        throw catalogError(`${label} contains invalid JSON near ${path || "<root>"}`);
      }
      const key = parseString();
      const childPath = path ? `${path}.${key}` : key;
      if (keys.has(key)) {
        throw catalogError(`${label} contains duplicate key ${childPath}`);
      }
      keys.add(key);
      skipWhitespace();
      if (source[index] !== ":") {
        throw catalogError(`${label} contains invalid JSON near ${childPath}`);
      }
      index += 1;
      parseValue(childPath);
      skipWhitespace();
      if (source[index] === ",") {
        index += 1;
        skipWhitespace();
      } else {
        break;
      }
    }
    index += 1;
  };
  skipWhitespace();
  parseValue("");
}

export function flattenCatalog(value, prefix = "") {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw catalogError(`${prefix || "<root>"} must be an object`);
  }
  const flattened = new Map();
  for (const [key, child] of Object.entries(value)) {
    if (key.length === 0) {
      throw catalogError(`${prefix || "<root>"} contains an empty key`);
    }
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof child === "string") {
      if (child.length === 0) {
        throw catalogError(`${path} must not be empty`);
      }
      flattened.set(path, child);
      continue;
    }
    for (const [nestedKey, nestedValue] of flattenCatalog(child, path)) {
      flattened.set(nestedKey, nestedValue);
    }
  }
  return flattened;
}

async function directoryNames(path) {
  return (await readdir(path, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
}

async function fileNames(path) {
  return (await readdir(path, { withFileTypes: true }))
    .filter((entry) => entry.isFile())
    .map((entry) => entry.name)
    .sort();
}

function assertExactMembers(actual, expected, subject) {
  const missing = expected.filter((value) => !actual.includes(value));
  const unsupported = actual.filter((value) => !expected.includes(value));
  if (missing.length > 0 || unsupported.length > 0) {
    throw catalogError(
      `${subject}; missing: ${missing.join(", ") || "none"}; unsupported: ${unsupported.join(", ") || "none"}`,
    );
  }
}

export async function validateMessageCatalogs(messagesRoot) {
  assertExactMembers(
    await directoryNames(messagesRoot),
    [...SUPPORTED_LOCALES].sort(),
    "locale directories must match the supported allowlist",
  );
  const expectedFiles = REQUIRED_NAMESPACES.map((namespace) => `${namespace}.json`).sort();
  const catalogs = new Map();
  const baselineKeys = new Map();

  for (const locale of SUPPORTED_LOCALES) {
    const localeRoot = `${messagesRoot}/${locale}`;
    assertExactMembers(
      await fileNames(localeRoot),
      expectedFiles,
      `${locale} namespace files must match the required set`,
    );
    const messages = {};
    for (const namespace of REQUIRED_NAMESPACES) {
      const path = `${localeRoot}/${namespace}.json`;
      let parsed;
      try {
        const source = await readFile(path, "utf8");
        parsed = JSON.parse(source);
        assertNoDuplicateJsonKeys(source, `${locale}/${namespace}.json`);
      } catch (error) {
        throw catalogError(`${locale}/${namespace}.json is not valid JSON: ${error.message}`);
      }
      const flattened = flattenCatalog(parsed);
      const keys = [...flattened.keys()].sort();
      if (locale === SUPPORTED_LOCALES[0]) {
        baselineKeys.set(namespace, keys);
      } else {
        assertExactMembers(
          keys,
          baselineKeys.get(namespace) ?? [],
          `${locale}/${namespace}.json keys must match en/${namespace}.json`,
        );
      }
      messages[namespace === "paper-jobs" ? "paperJobs"
        : namespace === "portfolio-records" ? "portfolioRecords"
          : namespace] = parsed;
    }
    const translator = createTranslator({ locale, messages });
    for (const [namespace, messagesForNamespace] of Object.entries(messages)) {
      for (const [key, message] of flattenCatalog(messagesForNamespace)) {
        const values = Object.fromEntries(
          [...message.matchAll(/\{([A-Za-z][A-Za-z0-9_]*)/g)].map((match) => [match[1], 1]),
        );
        try {
          translator(`${namespace}.${key}`, values);
        } catch (error) {
          throw catalogError(`${locale}/${namespace}.${key} has an invalid message format: ${error.message}`);
        }
      }
    }
    catalogs.set(locale, messages);
  }
  return catalogs;
}

async function main() {
  const messagesRoot = fileURLToPath(new URL("../messages", import.meta.url)).replaceAll("\\", "/");
  await validateMessageCatalogs(messagesRoot);
  process.stdout.write(
    `Validated ${SUPPORTED_LOCALES.length} locale catalogs across ${REQUIRED_NAMESPACES.length} namespaces.\n`,
  );
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main().catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
