# BREERO production activation evidence

```
PRODUCTION_ACTIVATION=BLOCKED
SSH_CHANGED=NO
SSH_COMMANDS_USED=NO
PRODUCTION_DEPLOYED=NO
```

No production activation was attempted. No deployment workflow was dispatched, no
release tag was created, no image was built or pushed, and no environment approval was
requested or granted.

## The exact missing non-SSH prerequisite

**An authenticated GitHub API credential for `appolon1908-hue/Breero.com`.**

```
$ gh auth status
You are not logged into any GitHub hosts.

$ echo "GH_TOKEN=${GH_TOKEN:-unset} GITHUB_TOKEN=${GITHUB_TOKEN:-unset}"
GH_TOKEN=unset GITHUB_TOKEN=unset
```

Git push over HTTPS works — commits reached `origin` — but every GitHub *API*
operation the activation sequence depends on is unavailable:

| Activation step | Requires | Available |
| --- | --- | --- |
| Inventory open PRs, issues, review threads | `repo` scope | NO |
| Inventory code scanning and Dependabot alerts | `security_events` scope | NO |
| Read exact-head check results | `repo` scope | NO |
| Open, update or merge pull requests | `repo` scope | NO |
| Create the annotated release tag and release | `repo` scope | NO |
| Grant the production environment approval | environment reviewer | NO |
| Dispatch the deployment workflow | `actions:write` | NO |
| Retrieve deployment evidence artifacts | `actions:read` | NO |

Two further prerequisites are missing on the executing host. Neither is SSH-related.

| Prerequisite | Blocks | Evidence |
| --- | --- | --- |
| Container runtime | Image build, digests, SBOM, provenance, signing, container scan, Compose render | `docker ps` → cannot connect to the Docker API at `npipe:////./pipe/dockerDesktopLinuxEngine` |
| PostgreSQL/PostGIS and Redis | Migration job, schema-revision verification, backup, restore validation, canary readiness | `which psql pg_dump` → absent |

## What must be true before activation is retried

Activation must not be attempted until these land, in this order. The reason is
ARCH-01 in the remediation ledger: **none of the eight branches on `origin`, including
`ops/portal-production-release`, fixes any of the six critical API findings.**
Activating the release stack as it stands would put password hashing on the event loop
and a production topology with no scheduler into production.

1. Critical API fixes merged (BE-01..BE-04, OPS-01, OPS-02).
2. `be/portal-read-models` reviewed, rebased and merged.
3. Observability reconciled into one implementation (OBS-02).
4. The portal stack merged in dependency order, base first.
5. SEC-01 triaged: 9 Dependabot alerts on `main`, 8 critical.
6. GATE 5, 6, 8 and 9 executed against a real staging runtime.

## Safe baseline capability state

If and when activation proceeds, this is the state the configuration validator
enforces. It is not a convention — `Settings.validate_production` raises and the API
refuses to boot if any of these is enabled in production.

```
PAYMENTS_ENABLED=NO
PAYOUTS_ENABLED=NO
AUTOMATIC_ASSIGNMENT_ENABLED=NO
MARKETPLACE_MATCHING_ENABLED=NO
MARKETPLACE_MESSAGING_ENABLED=NO
MARKETPLACE_REVIEWS_ENABLED=NO
PROVIDER_SELF_SERVICE_ENABLED=NO
MIDDLEWARE_DELIVERY_ENABLED=NO
EXTERNAL_EMAIL_ENABLED=controlled_canary
EXTERNAL_SMS_ENABLED=controlled_canary
```

## SSH statement

SSH was not used, configured, restarted or referenced at any point. No `ssh`, `scp`,
`sftp` or `rsync`-over-SSH command was run. No key, `authorized_keys` entry,
`sshd_config`, firewall rule, `fail2ban` policy, sudoers entry or cloud-init SSH
setting was read or modified. No deployment path introduced in this work depends on
SSH.
