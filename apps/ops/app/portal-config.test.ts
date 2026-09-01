import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { findContractProblems, type OpenApiDocument } from "@breero/portal";
import { opsPortalConfig } from "./portal-config";

const openapi = JSON.parse(
  readFileSync(new URL("../../api/openapi.json", import.meta.url), "utf8"),
) as OpenApiDocument;

describe("Operations portal configuration", () => {
  it("only reads endpoints that exist in the API contract", () => {
    // The previous configuration claimed capabilities were unavailable that had
    // shipped long before. This fails the build instead of letting prose drift.
    expect(findContractProblems(opsPortalConfig, openapi)).toEqual([]);
  });

  it("gives every blocked section a reason and a way out", () => {
    for (const section of opsPortalConfig.sections.filter((item) => !item.source)) {
      expect(section.blockedReason, `${section.slug} needs a reason`).toBeTruthy();
      expect(section.blockedOn, `${section.slug} needs an unblocking condition`).toBeTruthy();
    }
  });

  it("has unique section slugs", () => {
    const slugs = opsPortalConfig.sections.map((section) => section.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
  });
});
