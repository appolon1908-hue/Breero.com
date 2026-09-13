# Milestone 0 validation evidence

Accepted source inspected: `c8b5d31df80cd715ae189db9e16d6ff082c0d51f`.
Only documentation and inventory tooling are changed relative to that main revision.
The PR completion report records the final feature-branch SHA and its required CI.

| Check | Result | Scope |
|---|---|---|
| Inventory regeneration/equality | PASS | Source digests, API profiles, declared models, migration graph, routes, flags and workers |
| Six inventory acceptance tests | PASS | Includes hostile ambient environment isolation, nested/default/dark routes, audience evidence and narrative table coverage |
| Default OpenAPI equality | PASS | 96 paths / 116 operations; checked-in bytes match deterministic generated contract |
| Implemented route enumeration | PASS | 118 paths / 138 operations; `/metrics` separately inventoried; no handlers invoked |
| Frontend contract checker | PASS | 30 required paths; selected enums; payment routes absent in default artifact |
| Ruff for inventory scripts | PASS | Existing API Ruff configuration |
| Python compileall | PASS | scripts and API source; no business execution |
| Scope/classification regression scripts | PASS | Existing repository checks |
| Git whitespace | PASS | Changed files |
| Gitleaks, redacted output | PASS | Architecture documents and inventory scripts; no secrets found |
| Application/backend/PostgreSQL/PostGIS/concurrency/E2E suites | NOT RUN for final docs/tooling change | No runtime source or schema changed; no staging/production certification claimed |

Local Python runtime: 3.12.14; FastAPI 0.141.1; Pydantic 2.13.5; SQLAlchemy 2.0.52; Ruff 0.16.7. These identify the observed test environment and are not new dependency pins.

## CI/governance correction

The initial refresh of existing PR #128 still referenced an older base SHA in GitHub metadata. Refreshing its base to the actual main SHA corrected the changed-file scope. Initial checks attached to that old comparison are not final-head evidence.

An attempted optional Architecture baseline evidence workflow passed its inventory tests in [run 34747169880](https://github.com/appolon1908-hue/Breero.com/actions/runs/34747169880), but [the required orchestrator check](https://github.com/appolon1908-hue/Breero.com/actions/runs/34747169855) rejected the additional workflow as unapproved executable configuration. The optional workflow was removed. No disable marker, policy exception, allowlist change, skipped required check or approval bypass was added. The final source retains local acceptance tests and uses the existing required CI; workflow registration remains separate governed work.

Two initial Gitleaks findings were generated OpenAPI checksum field names, not credential values. Renaming those fields to `contract_sha256` preserved the computed digests and yielded a clean scan without suppressions or scanner changes.

## Acceptance remains external

The independent reviewer must approve the final commit after all required checks pass. Source inventory and CI results do not prove live identity, tenant isolation, host capacity, integrations, backup/restore, financial settlement or production readiness. Milestone 1 starts only after the baseline is accepted under the mission's dependency rule.
