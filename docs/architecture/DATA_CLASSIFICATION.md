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

## Retention ownership and current implementation

These are data categories to govern, not invented retention durations or legal advice. Exact schedules require approved product/platform policy before retention automation.

| Category | Authority | Executable retention status |
|---|---|---|
| Customer/contact/address and provider/worker records | BREERO | No complete export/deletion/retention pipeline established |
| Conversations and communications | BREERO intent; Klyrow/Telnexa transport | General conversations absent; transport callback/retention integration incomplete |
| Job evidence and compliance documents | BREERO plus central document authority | Metadata foundations only; central secure pipeline and retention absent |
| Financial ledger/payment/payout records | BREERO finance; Stripe settlement | Financial records exist; legal-hold/reversal/retention certification incomplete |
| Logs, traces and metrics | Codestra Loki/Tempo/Prometheus owners | Collection source exists; actual retention configuration not verified |
| Support cases and reviews | BREERO | General domains absent; no retention jobs established |
| Consent and preferences | BREERO | ConsentEvent, Suppression and PrivacyRequest foundations; completion/reconciliation gaps remain |

Local EmailAdapter/ConsoleEmailGateway logging includes recipient email. This is an existing confidential-data minimization gap; structured logs and trace IDs alone do not prove privacy compliance. Internal event diagnostics and payloads require explicit review before telemetry or analytics export. No real customer, provider or credential data was collected for this inventory.
