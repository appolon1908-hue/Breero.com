# Integration registry

Source baseline is recorded in [CURRENT_SYSTEM.md](CURRENT_SYSTEM.md). The complete local adapter classes and file digests are in [SOURCE_INVENTORY.json](SOURCE_INVENTORY.json). This table distinguishes implemented source from external platform services whose runtime was not inspected.

| Integration/provider | Source and direction | Classification | Remaining boundary or evidence |
|---|---|---|---|
| Keycloak | `domains/auth/security.py`, `dependencies.py`; inbound JWT/JWKS; web PKCE S256 in `apps/web/lib/keycloak.ts` | PARTIAL | Optional backend default; issuer/audience validation exists; machine client-credentials/principal separation, complete claim/tenancy negative matrix and live realm/client certification remain |
| OpenBao | `secret_files.py`, `config.py`, `openbao-secret-consumer.v1.json`, `OPENBAO-API-SECRETS.md`; injected credential files | PARTIAL | Production requires DB/Redis/JWT file bindings; file errors fail closed; platform workload identity, real mounts, rotation and revocation unverified |
| Middleware | `integrations/middleware.py`; outbound HTTPS with HMAC-V2 and client certificates | PARTIAL | Default off; four event types accepted; future inbox/reconciliation/shared envelope required |
| Odoo | `integrations/odoo.py`, `api/internal_odoo.py`, `odoo-addons/breero_crm` | DEPRECATED adapter; PARTIAL projection | Direct credential/enablement rejected at startup; legacy code remains; internal routes read/retry local outbox with role checks; transport is Middleware in current worker |
| Klyrow/email | `integrations/email.py`; HTTP EmailAdapter, SmtpEmailGateway, fake/console gateways and templates | PARTIAL legacy email; NOT_IMPLEMENTED named Klyrow contract | Direct legacy paths need governed Middleware delivery, versioned templates, live switch, suppression and durable delivery callbacks |
| Telnexa/SMS | `integrations/sms.py`; protocol, fake/unconfigured gateways, templates | STUB | No carrier transport, signed provider inbox, MT/DLR/MO or Telnexa quota/routing reconciliation |
| VICIdial | No BREERO adapter | NOT_IMPLEMENTED | Middleware owns calling integration; external configuration not inspected |
| Stripe | `integrations/stripe.py`, `domains/payments`, payment routes; direct API plus inbound webhook foundation | PARTIAL / default-dark routes | Preserve existing settlement foundation; complete duplicate/refund/dispute/timeout certification and platform adapter ownership review remain |
| Geoapify | `integrations/geocoding.py`, `domains/geography/providers.py`; direct HTTP geocoder and fake | PARTIAL / default-dark public routes | Backend coverage/timezone authority; full failure/manual-review policy and external adapter governance remain |
| Payout gateway | `integrations/payouts.py`; interface, fake and unconfigured implementations | STUB transport / PARTIAL finance | No live payout provider certification; finance task guards and reconciliation remain |
| Caddy/Kong/WAF | Compose external edge networks; no canonical Kong/WAF policy in this repository | PARTIAL definitions | TLS/gateway authority is platform; reconcile ingress, internal/metrics exposure and deployment topology |
| Prometheus | `observability.py`, `deploy/observability/prometheus-breero.yml` | PARTIAL | Six executable custom metric families; scrape/alert/runtime coverage unverified |
| Alloy/Loki | Structured logging plus Alloy and stack overlay files | PARTIAL | Shipping/redaction/retention/runtime verification required |
| OpenTelemetry/Tempo | API/DB/Redis/Celery instrumentation, OTLP collector overlay | PARTIAL / tracing dark | Full business-event and cross-Middleware/provider trace continuity unverified |
| Alertmanager | No complete BREERO alert rules/routing certification | NOT_IMPLEMENTED here | Prometheus -> Alertmanager -> Middleware; no direct Odoo writes |
| Grafana | External platform dashboards | NOT_IMPLEMENTED here | No accepted BREERO dashboard/certification evidence found |
| Superset | No reporting-store pipeline | NOT_IMPLEMENTED | Separate business events/reporting store; never transactional database write authority |
| Azure Service Bus/RabbitMQ | No approved business broker deployment/adapter here | NOT_IMPLEMENTED | Redis Celery transport is not evidence of the shared business-event bus |

## Existing event contract

Middleware currently posts `/api/v1/integrations/breero/events` and accepts only `breero.service_request.created`, `breero.contact_request.created`, `breero.provider_interest.created`, and `breero.lead_dispute.created`. It reuses OdooAdapter's pure envelope helper: event_id, event_type, schema_version, aggregate_id/version, occurred_at, idempotency_key, source and payload. It is not yet the mission's shared envelope: tenant_id, correlation_id, trace_id, event_version and subject_type/id/data are not all present in that body. Tenant/service/audience/environment/scope authentication headers exist and must not be confused with the business envelope.

BREERO's immutable DomainEvent carries event/aggregate type/id/version, timestamp, correlation ID and payload, but does not by itself provide the shared cross-product contract. Update these contracts additively with Middleware ownership and consumer compatibility evidence.

## Outbox and inbox evidence

`IntegrationEvent` and `OutboxService` already implement PostgreSQL persistence, `SKIP LOCKED` claims, 300-second leases, stale-lease reclamation, per-attempt claim tokens, exponential retry with jitter, terminal states and audited retry. Preserve this foundation.

Remaining correctness gaps from source review:

- Completion updates do not compare the claim token in a guarded database update, so claim fencing is not yet established when slow delivery outlives its lease.
- The worker's unknown-event branch returns normally; `OutboxService.process` then sets DELIVERED. Unknown events therefore can receive false delivery success, rather than staying local/recoverable as the comment says.
- Notification events dispatch through EmailAdapter before the CRM branch, without transactional-mode enforcement. The public-submission parking filter does not cover these notifications or every CRM aggregate.
- Middleware acknowledgements of queued/replayed/delivered all lead to the local delivery path. A queued receipt is not proof that the Odoo projection was applied; projection reconciliation needs separate status.
- No general durable integration inbox or signed Klyrow/Telnexa callback flow exists. Stripe webhook handling is a separate implemented foundation, not a universal inbox.

A subsequent focused safety PR must correct these gaps without enabling transport. This registry does not claim end-to-end deduplication, replay authorization completeness or financial reconciliation.

## Odoo write policy

Settings rejects ODOO_ENABLED=true, nonempty ODOO_API_KEY and ODOO_API_KEY_FILE before reading secret files in every environment. The worker sends allowed business events through Middleware. The mounted `/internal/v1/integrations/odoo/*` handlers access BREERO's own outbox and may enqueue an audited retry; they do not directly call Odoo's business API. Their Odoo naming/status fields are legacy and should be reconciled with Middleware projection semantics.

OdooAdapter still contains direct JSON-RPC methods. Its shared mapper/envelope code is used by existing foundations, so do not delete the whole module without separating those uses. Normal startup prohibition is source evidence; it does not establish that all deployed artifacts/external services comply. Odoo CRM add-on models remain external projection code. Prometheus, Grafana, Loki, Tempo, Alloy and exporters must never receive Odoo write credentials or mutate Odoo business records.

## Platform repository dependencies

| Authority | Repository / status |
|---|---|
| Email | `appolon1908-hue/klyrow.com`; external contract/runtime not inspected in this baseline |
| SMS | `appolon1908-hue/telnexa`; external contract/runtime not inspected |
| Secrets | `appolon1908-hue/Codestra-OpenBao`; local consumer contract accepted, runtime unverified |
| Integration control plane | `appolon1908-hue/Middleware-`; local signed adapter contract only |
| Telemetry | `Codestra-Telemetry`, `Codestra-Alloy`, `Codestra-Prometheus`, `Codestra-Loki`, `Codestra-Tempo`; external runtime unverified |
| Alerts/dashboards | `Codestra-Alertmanager`, `Codestra-Grafana-`; external runtime unverified |
| Infrastructure metrics | `Codestra-Node-Exporter`, `Codestra-cAdvisor`, `Codestra-Redis-Exporter`, `Codestra-Postgres-Exporter`, `Codestra-Blackbox-Exporter`; external runtime unverified |
| Analytics | `Superset`; reporting pipeline unimplemented in BREERO source |

Platform responsibilities remain external. No integration row is permission to send live messages, activate payments or write Odoo.
