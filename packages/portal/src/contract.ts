import type { PortalConfig } from "./types";

/**
 * Check a portal configuration against the API's own OpenAPI document.
 *
 * The previous portal configurations described capabilities as "awaiting a canonical
 * backend operation" that had in fact shipped months earlier. Nothing caught it,
 * because the claim lived in prose. This turns both halves of that claim into
 * something a test can fail on: a section that reads an endpoint must name one that
 * exists, and a section that says it is blocked must say why.
 */

export interface OpenApiDocument {
  paths: Record<string, Record<string, unknown>>;
}

const API_PREFIX = "/api/v1";

/** `/email/domains/abc-123/verification?verified=true` -> `/email/domains/{}/verification` */
function normalise(path: string): string[] {
  return path.split("?")[0]!.split("/").filter(Boolean);
}

function matches(actual: string[], template: string[]): boolean {
  if (actual.length !== template.length) return false;
  return template.every((segment, index) =>
    segment.startsWith("{") ? true : segment === actual[index],
  );
}

/** Every path in the document, as method -> list of segment templates. */
function index(document: OpenApiDocument): Map<string, string[][]> {
  const byMethod = new Map<string, string[][]>();
  for (const [path, operations] of Object.entries(document.paths)) {
    for (const method of Object.keys(operations)) {
      const key = method.toUpperCase();
      if (!byMethod.has(key)) byMethod.set(key, []);
      byMethod.get(key)!.push(normalise(path));
    }
  }
  return byMethod;
}

export interface ContractProblem {
  section: string;
  problem: string;
}

export function findContractProblems(
  config: PortalConfig,
  document: OpenApiDocument,
): ContractProblem[] {
  const byMethod = index(document);
  const problems: ContractProblem[] = [];

  const exists = (method: string, path: string): boolean => {
    const segments = normalise(`${API_PREFIX}${path}`);
    return (byMethod.get(method) ?? []).some((template) => matches(segments, template));
  };

  for (const section of config.sections) {
    if (section.source) {
      if (!exists("GET", section.source)) {
        problems.push({
          section: section.slug,
          problem: `reads GET ${section.source}, which is not in the API contract`,
        });
      }
      for (const action of section.actions ?? []) {
        // Actions build their path from a row, so probe with a placeholder id. Only
        // the literal segments are compared, which is what can actually be mistyped.
        const probe = action.path({ id: "00000000-0000-0000-0000-000000000000" });
        if (!exists(action.method, probe)) {
          problems.push({
            section: section.slug,
            problem: `action "${action.label}" calls ${action.method} ${probe}, which is not in the API contract`,
          });
        }
      }
    } else if (!section.blockedReason) {
      problems.push({
        section: section.slug,
        problem: "has no source and no blockedReason, so it would render as a silent blank",
      });
    }
  }

  return problems;
}
