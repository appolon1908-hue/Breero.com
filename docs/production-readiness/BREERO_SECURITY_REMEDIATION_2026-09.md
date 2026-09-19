# BREERO critical dependency remediation ? September 2026

Status: preflight recorded; remediation and merge pending. `SECURITY_GATE=BLOCKED`.

Canonical repository: `ingtrader21-spec/Breero.com` (repository ID 1331354808). `SECURITY_BASE_SHA=2292fd7533faa5752a3df7a8243e217447694367`. Both existing real worktrees are clean and unchanged; this work uses an isolated worktree. The prior verified 784-file source snapshot is preserved. No production or provider operation is authorized or performed.

## Observed dependency graph

[GHSA-5xrq-8626-4rwp](https://github.com/advisories/GHSA-5xrq-8626-4rwp) affects Vitest versions below 3.2.6 on the relevant release line. All eight direct development-dependency manifests declare `^2.1.8`, while root `pnpm.overrides.vitest=3.2.6` already resolves every workspace to patched Vitest 3.2.6 and Vite 6.4.3. One authoritative `pnpm-lock.yaml` controls them. Per-workspace `pnpm why vitest --depth Infinity --json` outputs are embedded in [preflight.json](../../artifacts/security-remediation/preflight.json).

| Alert | Direct manifest | Declared before | Resolved before |
|---|---|---|---|
| #1 | `apps/admin/package.json` | `^2.1.8` | `3.2.6` |
| #2 | `apps/ops/package.json` | `^2.1.8` | `3.2.6` |
| #3 | `apps/partner/package.json` | `^2.1.8` | `3.2.6` |
| #4 | `apps/web/package.json` | `^2.1.8` | `3.2.6` |
| #5 | `packages/api-client/package.json` | `^2.1.8` | `3.2.6` |
| #6 | `packages/portal/package.json` | `^2.1.8` | `3.2.6` |
| #7 | `packages/types/package.json` | `^2.1.8` | `3.2.6` |
| #8 | `packages/ui/package.json` | `^2.1.8` | `3.2.6` |

The remediation will pin all eight direct declarations to 3.2.6, matching the existing override and lockfile. No Vite/Vitest runtime major transition is required; the plan's major-upgrade assumption does not match the observed resolved graph. A frozen installation with pnpm 10.0.0 succeeded before changes. Characterization and dependency-policy tests will precede manifest edits.

## Remaining advisory scope

At preflight, Dependabot reports 8 critical, 0 high, and 11 medium alert instances. The medium Vitest/mocker advisory GHSA-82fw-gwwq-j7x9 requires 4.1.11; the PostCSS advisory GHSA-fxqj-rqcc-2cmp requires 8.5.23. These remain explicitly unresolved by this narrow critical-manifest remediation; no alert is dismissed or suppressed. Their presence must be carried into later certification evidence.

## Protected merge and execution gates

Main requires one independent approving review, approval of the latest push, resolved review threads, current `quality` and `orchestrator-contract` checks, and squash-only merge. Tasks 1?3 share this PR; Task 4 is its merge gate. Foundation recovery cannot begin until the security PR is merged and post-merge checks and critical/high alert counts are verified.

- [x] Refresh canonical main, permissions and effective branch rules.
- [x] Preserve existing worktrees and source snapshot.
- [x] Map eight alerts to workspace declarations and resolved dependency paths.
- [ ] Open the security PR with this preflight-only commit.
- [ ] Run baseline suites and characterization tests before manifest edits.
- [ ] Align direct declarations, regenerate the authoritative lockfile and validate all required gates.
- [ ] Obtain independent approval and protected merge.
- [ ] Verify exact post-merge main checks and resolved (not dismissed) alerts #1?#8.

`PRODUCTION_ACTIVATED=NO`. `LIVE_PROVIDER_CALLS=NO`. No architecture or capability changes are included.
