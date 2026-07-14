import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString, COMMENT_HEADER } from "openapi-typescript";

const snapshotUrl = new URL("../src/generated/openapi.json", import.meta.url);
const typesUrl = new URL("../src/generated/api-types.ts", import.meta.url);
const check = process.argv.includes("--check");

const document = JSON.parse(await readFile(snapshotUrl, "utf8"));
const nodes = await openapiTS(document);
const generated = `${COMMENT_HEADER}${astToString(nodes)}`;

if (check) {
  let current;
  try {
    current = await readFile(typesUrl, "utf8");
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") {
      console.error(
        `error: missing generated API types: ${fileURLToPath(typesUrl)}`,
      );
      process.exitCode = 1;
    } else {
      throw error;
    }
  }
  if (current !== undefined && current !== generated) {
    console.error(
      "error: generated API types are stale; run `npm --prefix web run contracts:generate`",
    );
    process.exitCode = 1;
  }
} else {
  await writeFile(typesUrl, generated, "utf8");
}
