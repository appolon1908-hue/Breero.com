import { describe, expect, it } from "vitest";
import { findContractProblems, type OpenApiDocument } from "./contract";
import type { PortalConfig } from "./types";

const DOCUMENT: OpenApiDocument = {
  paths: {
    "/api/v1/jobs": { get: {} },
    "/api/v1/operations/dispatcher/queue": { get: {} },
    "/api/v1/operations/dispatcher/queue/{request_id}": { patch: {} },
    "/api/v1/operations/vendors/{vendor_id}/status": { patch: {} },
    "/api/v1/admin/provider-applications/{application_id}/approve": { post: {} },
    "/api/v1/provider/skills/{provider_skill_id}": { delete: {} },
  },
};

function config(sections: PortalConfig["sections"]): PortalConfig {
  return { name: "Test", eyebrow: "Test", allowedRoles: ["operations"], sections };
}

describe("findContractProblems", () => {
  it("accepts a section whose source exists", () => {
    expect(
      findContractProblems(
        config([{ slug: "jobs", label: "Jobs", description: "d", source: "/jobs" }]),
        DOCUMENT,
      ),
    ).toEqual([]);
  });

  it("rejects a source that is not in the contract", () => {
    const problems = findContractProblems(
      config([{ slug: "jobs", label: "Jobs", description: "d", source: "/job" }]),
      DOCUMENT,
    );
    expect(problems).toHaveLength(1);
    expect(problems[0]!.problem).toContain("not in the API contract");
  });

  it("matches templated path parameters", () => {
    expect(
      findContractProblems(
        config([
          {
            slug: "queue",
            label: "Queue",
            description: "d",
            source: "/operations/dispatcher/queue",
            actions: [
              {
                label: "Start",
                method: "PATCH",
                path: (row) => `/operations/dispatcher/queue/${String(row.id)}`,
              },
            ],
          },
        ]),
        DOCUMENT,
      ),
    ).toEqual([]);
  });

  it("catches an action that uses the wrong verb", () => {
    const problems = findContractProblems(
      config([
        {
          slug: "vendors",
          label: "Providers",
          description: "d",
          source: "/jobs",
          actions: [
            {
              // The route exists, but only as PATCH.
              label: "Suspend",
              method: "POST",
              path: (row) => `/operations/vendors/${String(row.id)}/status`,
            },
          ],
        },
      ]),
      DOCUMENT,
    );
    expect(problems).toHaveLength(1);
    expect(problems[0]!.problem).toContain("POST");
  });

  it("ignores a query string when matching", () => {
    expect(
      findContractProblems(
        config([
          {
            slug: "apps",
            label: "Applications",
            description: "d",
            source: "/jobs",
            actions: [
              {
                label: "Approve",
                method: "POST",
                path: (row) => `/admin/provider-applications/${String(row.id)}/approve?notify=true`,
              },
            ],
          },
        ]),
        DOCUMENT,
      ),
    ).toEqual([]);
  });

  it("does not confuse paths of a different depth", () => {
    const problems = findContractProblems(
      config([
        {
          slug: "skills",
          label: "Skills",
          description: "d",
          source: "/jobs",
          actions: [
            {
              label: "Remove",
              method: "DELETE",
              path: (row) => `/provider/skills/${String(row.id)}/extra`,
            },
          ],
        },
      ]),
      DOCUMENT,
    );
    expect(problems).toHaveLength(1);
  });

  it("flags a blocked section with no explanation", () => {
    const problems = findContractProblems(
      config([{ slug: "earnings", label: "Earnings", description: "d" }]),
      DOCUMENT,
    );
    expect(problems).toHaveLength(1);
    expect(problems[0]!.problem).toContain("silent blank");
  });

  it("accepts a blocked section that explains itself", () => {
    expect(
      findContractProblems(
        config([
          {
            slug: "earnings",
            label: "Earnings",
            description: "d",
            blockedReason: "No provider-scoped endpoint exists.",
          },
        ]),
        DOCUMENT,
      ),
    ).toEqual([]);
  });

  it("reports every problem rather than stopping at the first", () => {
    const problems = findContractProblems(
      config([
        { slug: "a", label: "A", description: "d", source: "/missing-one" },
        { slug: "b", label: "B", description: "d", source: "/missing-two" },
        { slug: "c", label: "C", description: "d" },
      ]),
      DOCUMENT,
    );
    expect(problems.map((problem) => problem.section)).toEqual(["a", "b", "c"]);
  });
});
