# System ownership

This is the normative ownership boundary for BREERO on Codestra.

| Capability | Authority | BREERO boundary |
|---|---|---|
| Marketplace transactional state | BREERO PostgreSQL | Authoritative |
| Customers, requests, bookings, jobs | BREERO | Authoritative |
| Providers, workers, matching, reviews | BREERO | Authoritative |
| Authentication | Keycloak | BREERO validates identity; it must not become the production identity provider |
| Business authorization and record policy | BREERO | Server-enforced |
| TLS/host ingress | Caddy | External platform dependency |
| API gateway/policies | Kong | External platform dependency |
| Secrets and PKI | OpenBao | BREERO consumes injected secrets |
| Cross-system workflows and writes | Middleware | BREERO publishes/consumes governed events |
| Email transport | Klyrow | BREERO owns intent, template variables and business state |
| SMS transport | Telnexa | BREERO owns intent, consent and business state |
| Calling | VICIdial | Accessed through Middleware |
| CRM/ERP projection | Odoo | Projection only; never marketplace truth |
| Metrics, logs, traces | Prometheus, Loki, Tempo | BREERO emits safe telemetry |
| Telemetry collection | Alloy/OpenTelemetry | External platform dependency |
| Alerts | Alertmanager | Notifications route through Middleware |
| Operational visualization | Grafana | Read-only visualization |
| Business analytics | Superset/reporting store | Separate from operational telemetry |
| Infrastructure metrics | Codestra exporters | External platform dependency; no business-data writes |

## Mandatory Odoo boundary

No Prometheus, Grafana, Loki, Tempo, Alloy, exporter, browser, or BREERO business handler may write Odoo directly. The only approved production direction is `business/operational event -> Middleware -> authorized Odoo adapter`. Middleware owns authentication, authorization, mapping, schema translation, deduplication, idempotency, retry, audit, dead letters, replay, and write policy.

The legacy `app.integrations.odoo` adapter retains direct JSON-RPC methods and shared pure mapping/envelope helpers. Current Settings rejects direct Odoo enablement and credentials before reading secret files in every environment. The actual `/internal/v1/integrations/odoo` router reads/retries BREERO outbox records; it is not an Odoo business-write endpoint. The worker uses Middleware. Keep internal routes behind approved ingress and separate legacy helpers before removing the adapter; source restrictions are not deployed-runtime certification.

Stripe settlement and Geoapify currently use direct provider adapters. Preserve their accepted foundations while the owning integration workstreams reconcile them with the mission's governed cross-system boundary. No new transport authority is introduced by this inventory.
