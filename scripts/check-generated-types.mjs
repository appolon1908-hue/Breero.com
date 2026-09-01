// Fail when the committed OpenAPI types drift from the contract they came from.
//
// `check-frontend-openapi.mjs` proves the routes the frontend needs exist. It says
// nothing about their shape, so a backend rename of a field ships green and breaks at
// runtime. This regenerates the types and compares them to the committed output.
//
// The generator is invoked through `process.execPath` rather than the `.bin` shim so
// this works identically on Windows, where spawning a `.cmd` without a shell fails.
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const cli = join(dirname(require.resolve("openapi-typescript/package.json")), "bin", "cli.js");

const committed = "packages/types/src/generated.ts";
const scratch = mkdtempSync(join(tmpdir(), "breero-types-"));
const candidate = join(scratch, "generated.ts");

try {
  execFileSync(process.execPath, [cli, "apps/api/openapi.json", "-o", candidate], {
    stdio: "pipe",
  });

  // The committed file is generator output verbatim and is prettier-ignored, so the
  // only difference that can appear here is a real contract change.
  const normalise = (text) => text.replace(/\r\n/g, "\n").trimEnd();
  if (normalise(readFileSync(committed, "utf8")) !== normalise(readFileSync(candidate, "utf8"))) {
    console.error(
      `${committed} is out of date with apps/api/openapi.json.\n` +
        "The API contract changed without the frontend types being regenerated.\n" +
        "Run: pnpm gen:types",
    );
    process.exit(1);
  }
  console.log("Generated OpenAPI types match apps/api/openapi.json.");
} finally {
  rmSync(scratch, { recursive: true, force: true });
}
