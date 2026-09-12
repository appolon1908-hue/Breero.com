# Integration registry

| Integration | Direction | Current implementation | State | Target authority / action |
|---|---|---|---|---|
| Keycloak | inbound identity | Optional JWT/JWKS validation | PARTIAL/DARK | Make canonical issuer authoritative and fail closed |
| OpenBao | secret injection | `*_FILE` settings for core credentials | PARTIAL | Platform-managed workload identity and short-lived secrets |
| Middleware | outbound events | HTTPS adapter, HMAC/mTLS settings, outbox worker | PARTIAL/DARK | Sole cross-system control plane |
| Odoo | inbound/internal and legacy adapter | Internal router, adapter, CRM add-on | DEPRECATED risk | All production writes through Middleware only |
| Klyrow email | outbound/callback | Generic email adapter and SMTP configuration | STUB | Outbox -> Middleware -> Klyrow; signed callbacks via Middleware |
| Telnexa SMS | outbound/DLR/MO | Generic SMS adapter/provider configuration | STUB | Outbox -> Middleware -> Telnexa; DLR/MO via durable inbox |
| VICIdial | calling | No complete BREERO adapter | NOT_IMPLEMENTED | Middleware-governed integration |
| Stripe | payment/webhook | Intent, webhook and refund foundations | PARTIAL/DARK | Verified webhook is settlement authority |
| Geocoding | request/response | Geoapify provider abstraction | PARTIAL/DARK | Backend remains coverage authority |
| Payout provider | outbound/reconciliation | Generic adapter and finance workflow | PARTIAL/DARK | Finance-controlled, reconciled adapter |
| Prometheus | telemetry | No complete exposition in baseline | STUB | Codestra-Prometheus |
| Loki | logs | Structured logs only; no proven shipping | STUB | Alloy -> Codestra-Loki |
| Tempo/OpenTelemetry | traces | Correlation IDs, no distributed trace pipeline | NOT_IMPLEMENTED | OTel/Alloy -> Codestra-Tempo |
| Alertmanager | operational alerts | No repository alert routing | NOT_IMPLEMENTED | Alertmanager -> Middleware -> approved channel |
| Grafana | visualization | External only | NOT_IMPLEMENTED here | Read-only operational dashboards |
| Superset | analytics | No reporting-store pipeline | NOT_IMPLEMENTED | Business events -> reporting store -> Superset |

## Event reliability inventory

PostgreSQL transactional outbox processing exists, with retries from Celery. A shared Codestra envelope, durable inbox, explicit leases/stale-lease recovery, governed DLQ, replay authorization, and end-to-end reconciliation are incomplete. Unknown events currently remain local. Provider callbacks do not yet form one certified ingress path.

No integration row in this registry is permission to enable live delivery.
