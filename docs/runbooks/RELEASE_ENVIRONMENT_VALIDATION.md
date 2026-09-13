# Explicit environment validation

Milestone 1 / PR #99 requires `APP_ENV` to be set to exactly one of
`development`, `test`, `staging`, or `production`. There is no implicit default.
This preserves the accepted Keycloak, OpenBao, capability and CORS safeguards;
it prevents an omitted or misspelled environment from skipping release checks.

Before starting a candidate, verify that its approved environment configuration
contains the exact environment name. Do not dump the environment or Settings
object to prove this. File-backed secrets must retain their existing ownership,
private modes and read-only mount requirements. Validating APP_ENV does not
replace credential, identity, readiness or deployment preflight checks.

| Configuration | Expected result |
|---|---|
| APP_ENV missing from both environment and .env | Startup validation fails |
| Unknown, empty, differently cased or whitespace-padded value | Startup validation fails |
| Explicit development/test | Existing development/test behavior |
| Explicit staging | Existing staging credential and ingress checks |
| Explicit production | Existing production file-secret and dark-capability checks |

No capability value is changed by this fix. No schema, OpenAPI or frontend
contract change is expected. The earlier architecture inventory remains a dated
source checkpoint; this runbook records the additive environment requirement.

## Validation and recovery

Run `APP_ENV=test pytest tests/test_production_config.py tests/test_openbao_secret_files.py`
from the API environment, then the full suite against an isolated PostgreSQL/PostGIS
and Redis test environment. The regression checks cover valid file-secret startup
and reject missing/invalid environment names. OpenBao tests explicitly select test
mode so failures continue to verify secret handling rather than an unrelated
missing-environment error.

If a candidate fails because APP_ENV is absent or invalid, correct the approved
configuration before restart; do not relax validation. Runtime activation remains
a separate release. If a code rollback is required, revert the eventual PR squash
commit and preserve explicit valid environment configuration. No data rollback is
needed; never use rollback as authorization to activate a dark capability.
