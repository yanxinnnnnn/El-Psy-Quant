// @vitest-environment node

import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import {
  REQUIRED_NAMESPACES,
  REQUIRED_ERROR_CODES,
  SUPPORTED_LOCALES,
  assertErrorPresentationCatalog,
  assertNoDuplicateJsonKeys,
  flattenCatalog,
  validateMessageCatalogs,
} from "./check-messages.mjs";

const temporaryRoots = [];

afterEach(async () => {
  await Promise.all(temporaryRoots.splice(0).map((path) => rm(path, { recursive: true, force: true })));
});

async function validCatalogRoot() {
  const root = await mkdtemp(join(tmpdir(), "el-psy-quant-messages-"));
  temporaryRoots.push(root);
  for (const locale of SUPPORTED_LOCALES) {
    await mkdir(join(root, locale));
    for (const namespace of REQUIRED_NAMESPACES) {
      const value = namespace === "common"
        ? { metadata: { title: `${locale} title` } }
        : namespace === "errors"
          ? {
              categories: Object.fromEntries(
                ["authentication", "not_found", "invalid", "conflict", "unavailable", "protocol", "internal", "unknown"]
                  .map((category) => [category, `${locale} ${category}`]),
              ),
              technical: Object.fromEntries(
                ["title", "operation", "httpStatus", "entity", "errorCode", "requestId", "backendMessage"]
                  .map((field) => [field, `${locale} ${field}`]),
              ),
              ...Object.fromEntries(
                REQUIRED_ERROR_CODES.map((code) => [
                  code,
                  {
                    title: `${locale} ${code} title`,
                    explanation: `${locale} ${code} explanation`,
                    recovery: `${locale} ${code} recovery`,
                  },
                ]),
              ),
            }
        : { value: `${locale} ${namespace}` };
      await writeFile(join(root, locale, `${namespace}.json`), JSON.stringify(value), "utf8");
    }
  }
  return root;
}

describe("message catalog validation", () => {
  it("loads exact matching en and zh-CN catalogs", async () => {
    await expect(validateMessageCatalogs(await validCatalogRoot())).resolves.toBeInstanceOf(Map);
  });

  it("rejects unsupported locale directories", async () => {
    const root = await validCatalogRoot();
    await mkdir(join(root, "fr"));
    await expect(validateMessageCatalogs(root)).rejects.toThrow(/unsupported: fr/);
  });

  it("rejects missing namespaces and translated key drift", async () => {
    const root = await validCatalogRoot();
    await rm(join(root, "zh-CN", "errors.json"));
    await expect(validateMessageCatalogs(root)).rejects.toThrow(/missing: errors.json/);

    const secondRoot = await validCatalogRoot();
    await writeFile(join(secondRoot, "zh-CN", "common.json"), JSON.stringify({ metadata: { heading: "标题" } }), "utf8");
    await expect(validateMessageCatalogs(secondRoot)).rejects.toThrow(/keys must match/);
  });

  it("rejects malformed JSON and non-string leaves", async () => {
    const root = await validCatalogRoot();
    await writeFile(join(root, "en", "errors.json"), "{", "utf8");
    await expect(validateMessageCatalogs(root)).rejects.toThrow(/not valid JSON/);
    expect(() => flattenCatalog({ invalid: 1 })).toThrow(/invalid must be an object/);
    expect(() => assertNoDuplicateJsonKeys('{"key":"one","key":"two"}', "duplicate.json"))
      .toThrow(/duplicate key key/);
  });

  it("rejects a missing stable error or incomplete presentation fields", () => {
    const complete = {
      categories: Object.fromEntries(
        ["authentication", "not_found", "invalid", "conflict", "unavailable", "protocol", "internal", "unknown"]
          .map((category) => [category, category]),
      ),
      technical: Object.fromEntries(
        ["title", "operation", "httpStatus", "entity", "errorCode", "requestId", "backendMessage"]
          .map((field) => [field, field]),
      ),
      ...Object.fromEntries(
        REQUIRED_ERROR_CODES.map((code) => [
          code,
          { title: "Title", explanation: "Explanation", recovery: "Recovery" },
        ]),
      ),
    };
    const withoutCode = { ...complete };
    delete withoutCode.paper_run_invalid;
    expect(() => assertErrorPresentationCatalog(withoutCode, "en"))
      .toThrow(/missing: paper_run_invalid/);
    expect(() => assertErrorPresentationCatalog({
      ...complete,
      not_found: { title: "Title", explanation: "Explanation" },
    }, "en")).toThrow(/not_found fields.*missing: recovery/);
  });
});
