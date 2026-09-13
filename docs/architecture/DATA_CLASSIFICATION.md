# Data classification and handling baseline

| Class | Examples | Baseline handling requirement |
|---|---|---|
| PUBLIC | Service catalog, public provider-approved profile, published reviews | Integrity controls; cache and publish only approved fields |
| INTERNAL | Operational reason codes, non-sensitive configuration, aggregate KPIs | Authenticated workforce access; do not publish by default |
| CONFIDENTIAL | Customer/provider contact data, addresses, conversations, quotes, schedules, support cases | Tenant and record policy, encryption in transit/at rest, audited access, minimized telemetry |
| RESTRICTED | Credentials/tokens, tax identifiers, background checks, licenses/insurance evidence, job evidence/signatures, payment and payout records, fraud notes | Least privilege, strong audit, secret/document isolation, no raw telemetry, explicit retention/legal hold |

## Store and flow rules

BREERO PostgreSQL stores marketplace records. Redis must contain only bounded operational/cache/queue data and never become a system of record. OpenBao owns secrets and PKI. Klyrow and Telnexa receive only the data required for an authorized message. Middleware receives the minimum governed event payload required for external workflows. Odoo holds a projection, not canonical marketplace state. Operational telemetry must use safe identifiers and avoid customer content or credentials. Business analytics must flow to a separate reporting store before Superset.

## Retention status

Consent/privacy request persistence exists, but executable retention schedules, export completion, deletion/anonymization, legal hold, communications retention, job-evidence retention, financial retention, and telemetry retention are PARTIAL or NOT_IMPLEMENTED. Until policies are approved, deletion must not silently destroy legally required financial/audit records and retention jobs must not be enabled.

## Never log

Passwords, access/refresh/reset tokens, API keys, webhook secrets, OpenBao material, SMTP/SMPP credentials, raw payment data, full document contents, and unrestricted internal trust notes are prohibited from logs, traces, metrics, and analytics labels.
