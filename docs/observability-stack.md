# Breero observability, analytics and secrets boundary

The approved stack is recorded in [stack-contract.json](../deploy/observability/stack-contract.json).
The repository owner for every component below is `appolon1908-hue`.

## Responsibilities

| Repository | Responsibility |
| --- | --- |
| [Codestra-Prometheus](https://github.com/appolon1908-hue/Codestra-Prometheus) | Metrics collection, recording rules, alert rules and service health |
| [Codestra-Alertmanager](https://github.com/appolon1908-hue/Codestra-Alertmanager) | Alert routing, grouping, escalation and Middleware notifications |
| [Codestra-Grafana-](https://github.com/appolon1908-hue/Codestra-Grafana-) | Infrastructure, application, API, Odoo, Middleware, SMS, email and calling dashboards |
| [Codestra-Telemetry](https://github.com/appolon1908-hue/Codestra-Telemetry) | OpenTelemetry collection and telemetry standards |
| [Codestra-Alloy](https://github.com/appolon1908-hue/Codestra-Alloy) | Metrics, logs and traces collection and forwarding |
| [Codestra-Loki](https://github.com/appolon1908-hue/Codestra-Loki) | Centralized application and infrastructure logs |
| [Codestra-Tempo](https://github.com/appolon1908-hue/Codestra-Tempo) | Distributed API and service tracing |
| [Codestra-Node-Exporter](https://github.com/appolon1908-hue/Codestra-Node-Exporter) | Linux CPU, memory, disk, filesystem and network metrics |
| [Codestra-cAdvisor](https://github.com/appolon1908-hue/Codestra-cAdvisor) | Docker and container resource monitoring |
| [Codestra-Redis-Exporter](https://github.com/appolon1908-hue/Codestra-Redis-Exporter) | Redis health, memory, connections, commands and queue metrics |
| [Codestra-Blackbox-Exporter](https://github.com/appolon1908-hue/Codestra-Blackbox-Exporter) | HTTP, HTTPS, TCP, DNS, endpoint, TLS and availability probes |
| [Codestra-Postgres-Exporter](https://github.com/appolon1908-hue/Codestra-Postgres-Exporter) | PostgreSQL monitoring |
| [Superset](https://github.com/appolon1908-hue/Superset) | Read-only business intelligence, KPI reporting and analytics |
| [Codestra-OpenBao](https://github.com/appolon1908-hue/Codestra-OpenBao) | Credentials, certificates, tokens and monitoring secrets |

## Signal and control flows

Servers, Apps, Odoo, Middleware, Klyrow, Telnexa, VICIdial, Keycloak, Kong and Caddy
supply telemetry through exporters, OpenTelemetry and Alloy. Prometheus stores metrics,
Loki stores logs, and Tempo stores traces. Prometheus alert rules and optional Loki ruler
rules send alerts to Alertmanager; trace-derived alerts need a metrics/rule path first.
Alertmanager groups and routes operational events to Middleware. Grafana queries the
three telemetry backends for visualization; data does not have to pass through
Alertmanager or Middleware before Grafana can display it.

Choose one owner per collection job. Alloy and the OpenTelemetry collector are supported
collection paths, not a requirement to collect and forward each signal twice. Exporter
scrapes may go directly to Prometheus; collector metrics forwarding requires the receiving
Prometheus remote-write endpoint to be explicitly configured. Contract edges describe
allowed signal relationships, not listeners or automatically enabled features.

Business data has a separate path into Superset through approved read models, preferably
a replica or curated warehouse. Its database role must be read-only and tenant-scoped.
Superset must not receive Odoo write credentials or application-owner database credentials.
OpenBao protects credentials, certificates and tokens across both paths; it is not a
telemetry store or business writer.

## Odoo write boundary

Grafana, Prometheus, Loki, Tempo, Alloy, OpenTelemetry collectors, exporters, Alertmanager
and Superset must not directly write business data into Odoo. Middleware alone holds the
Odoo integration write identity and applies authentication, scope, validation, idempotency,
audit and durable delivery before an approved write.

Breero already rejects `ODOO_ENABLED=true` in protected runtime settings. Its existing
[Middleware event contract](breero-middleware-integration.md) permits four Breero business
events. Alertmanager notifications must use Middleware's separately reviewed monitoring
ingress; do not send Alertmanager payloads to Breero's business-event endpoint or add
arbitrary Odoo model/method dispatch to that endpoint. An operational alert does not
implicitly authorize an Odoo write.

Enforce this boundary in deployment as well as configuration:

- Give telemetry services no Odoo business-write credentials or business command scopes.
- Permit collector egress only to approved telemetry receivers and monitored health/metrics
  endpoints. Odoo monitoring access must be read-only and explicitly limited.
- Allow Alertmanager notifications only to the approved authenticated Middleware ingress.
  Use its actual monitoring payload/authentication contract when provisioning the receiver.
- Keep telemetry backends and exporter endpoints private. Grafana uses provisioned server-side
  datasource credentials and tenant-scoped access; never expose backend credentials in browsers.
- Use separate least-privilege identities for PostgreSQL and Redis exporters. Do not mount the
  Breero API environment file, application database credentials or Odoo credentials into collectors.
- Deliver OpenBao-managed credentials through read-only secret files with renewal and rotation;
  restrict access to each workload's secret paths. Do not embed tokens in labels, URLs or dashboards.

The JSON validator checks declared relationships, not live network policy, database grants,
OpenBao policies or arbitrary code/configuration elsewhere in this or another repository.
Changing its allowlist requires architecture review. Passing it is not runtime certification.

## Breero integration status

The base of this change is `a5fc9921cbd6b71f83f1660fc505f02316572256`. It provides
`/health/live` and `/health/ready`; it does not yet provide the proposed `/metrics`
instrumentation. The following existing work remains separate:

| Work | Pull request | Dependency |
| --- | --- | --- |
| Metrics, tracing, heartbeat and log collection | [#106](https://github.com/appolon1908-hue/Breero.com/pull/106) | Validate and integrate instrumentation before enabling collection |
| Shared monitoring onboarding | [#125](https://github.com/appolon1908-hue/Breero.com/pull/125) | Register actual service units and deployment identity |
| OpenBao API secret-file integration | [#127](https://github.com/appolon1908-hue/Breero.com/pull/127) | Review secret delivery and rotation before activation |

`activation_enabled=false` and `runtime_coverage=unverified` accurately describe this
contract's initial state. This change defines and checks architecture; it does not merge
these PRs, install the shared stack, change live credentials or deploy to Breero's server.
Service names, addresses, identities and tenant mappings must come from the approved release
inventory, not inferred hostnames. No production Alertmanager URL is invented here.

## Activation and evidence

1. Integrate and validate the pending instrumentation and secret-file changes against the
   chosen production Compose manifest. Retain `ODOO_ENABLED=false`.
2. Register API, worker, web and portal service units actually present in that release, with
   environment, tenant, source deployment, Git SHA, image digest and configuration digest.
3. Provision private collection targets, a single collector owner per signal, OpenBao workload
   policies, Grafana datasources and the read-only Superset data source in their owning repositories.
4. Configure Alertmanager's approved Middleware monitoring receiver with its required TLS and
   authentication. Validate routing, grouping, escalation, delivery and resolved notifications.
5. In staging, capture fresh metrics, redacted logs and a correlated trace. Check route-template
   labels and bounded cardinality; exclude bodies, query strings, tokens, email addresses and
   customer identifiers. Verify exporter database identities cannot mutate business data.
6. Exercise a controlled alert and recovery. Record Middleware's audit receipt and deduplication
   result, and confirm that any Odoo effect requires a separately approved business mapping.
7. Verify secret rotation, telemetry outage behavior, backup/restore and rollback. Attach exact
   commit CI and immutable release evidence before updating coverage and activating production.

For rollback, restore the prior immutable application/collector configuration and approved
secret versions. Disable telemetry forwarding and notification routes independently of the
business outbox. Preserve operational audit history and existing business delivery semantics.

Run the repository checks from the root:

```sh
python3 scripts/observability/validate_contract.py
python3 -m unittest discover -s scripts/observability -p 'test_*.py' -v
```
