# BREERO observability

Before this existed, `METRICS_ENABLED` defaulted to true and gated nothing: there was
no `/metrics`, no Prometheus client, no tracing, and no way to answer "is the outbox
draining" without a `psql` session.

## What is exposed

`GET /metrics` on the API, in Prometheus text format. It returns 404 when
`METRICS_ENABLED` is off. In production `METRICS_TOKEN` is required — the endpoint
names route templates and internal aggregates, and although it is only scraped over
the private network, the token means a proxy misconfiguration is not on its own enough
to expose it. Comparison is constant-time.

### Request metrics

| Series | Notes |
| --- | --- |
| `breero_http_requests_total{method,route,status}` | `route` is the **route template**, never the raw path, so a UUID in a URL cannot mint a new series. Requests that match no route share `route="<unmatched>"`. |
| `breero_http_request_duration_seconds{method,route}` | Histogram, buckets from 5ms to 10s. |
| `breero_http_requests_in_flight` | Decremented on every exit path, including a raise. |

### Domain metrics

| Series | The question it answers |
| --- | --- |
| `breero_outbox_events{status}` | Is the outbox draining? Every status is reported, including zeros. |
| `breero_outbox_oldest_undelivered_age_seconds` | How far behind is delivery? |
| `breero_booking_holds_overdue` | Is capacity being released? |
| `breero_payments{status}` | Payment state distribution. |
| `breero_scheduled_task_last_success_timestamp_seconds{task}` | Is the scheduler alive? |
| `breero_scheduled_task_last_success_age_seconds{task}` | How long since it last was? |

## How the two kinds are collected

The API runs `uvicorn --workers 2`, so a scrape reaches one worker at random.

**Request counters** are per-process and aggregated through `prometheus_client`'s
multiprocess mode. Without it Prometheus would see two independent counters interleaved
and read the difference as repeated resets. It needs `PROMETHEUS_MULTIPROC_DIR` to be
writable — it points at `/tmp/prometheus`, because the production container runs
`read_only: true` with only `/tmp` mounted read-write.

**Domain gauges** are absolute facts, not per-worker tallies. Summing them across
workers would multiply them by the worker count, so they are declared
`multiprocess_mode="livemostrecent"` and read straight from Postgres or Redis at scrape
time. Whichever worker serves the scrape reports the true value.

Database collection is wrapped: a Postgres failure logs and returns rather than failing
the scrape, because a failed scrape marks the target down and hides the request metrics
that are still perfectly good.

## The scheduler heartbeat

This is the one worth understanding, because it exists to catch a failure that has
already happened.

`deploy/production/docker-compose.backend.yml` shipped without a `beat` service while
`docker-compose.production.yml` at the repository root had one. Nothing failed loudly.
The outbox simply stopped being published and booking holds stopped being released —
and with capacity fixed at one appointment per interval, the schedule quietly fills up
and stops offering appointments.

Both files now define a `scheduler`, and `test_a_topology_with_a_worker_also_runs_beat`
asserts that every compose file defining a Celery worker also runs beat. The heartbeat
below is the second line of defence: the topology can be right and the process can
still be dead.

Each periodic task stamps `breero:heartbeat:<task>` in Redis **after it succeeds**. The
worker and the API are separate containers, so the signal cannot be an in-process
gauge. A task that raises leaves the previous timestamp alone and lets its age climb: a
failing task must not look alive.

A task that has never run leaves no key, reported as an explicit `0` rather than a
missing series, so `== 0` alerts on a scheduler that never started at all. Age is `-1`
in that case, to distinguish "never ran" from "ran a moment ago".

`test_every_scheduled_task_has_a_heartbeat` asserts the set of stamped tasks equals the
set in `beat_schedule`, so adding a periodic task without a heartbeat fails CI.

## Tracing

Off by default. Set `TRACING_ENABLED=true` and point `OTEL_EXPORTER_ENDPOINT` at the
collector. FastAPI, SQLAlchemy and Celery are instrumented; health and metrics paths are
excluded because they are scraped every few seconds and carry no diagnostic value.

Spans carry `breero.request_id` and `breero.correlation_id`, the same ids the structured
logs use and the same correlation id payment events now persist into the outbox — so a
trace, its logs, and the integration events it produced can be pivoted between.

The Celery worker instruments on `worker_process_init` rather than at import, because
Celery forks after module load and a tracer provider created before the fork leaves its
exporter thread behind in the parent.

## Running the stack

```bash
docker compose \
  -f deploy/production/docker-compose.backend.yml \
  -f deploy/observability/docker-compose.observability.yml up -d
```

Prometheus retention is deliberately short (15 days / 8GB): this is an alerting store,
and the host has one disk that PostgreSQL also lives on. Grafana is the only service on
the edge network and is never published directly — reach it through an SSH tunnel or an
authenticated proxy route.

**Alertmanager has no receiver configured.** That is deliberate rather than a
placeholder that would silently swallow pages. Configure a real destination in
`deploy/observability/alertmanager.yml` before relying on any of this.

## Alerts

`deploy/observability/alerts.yml`, validated in CI by `promtool check rules` — a typo in
an expression should not be discovered when the alert fails to fire.

| Alert | Severity | Fires when |
| --- | --- | --- |
| `SchedulerNeverRan` | critical | A task has no heartbeat at all after 10m |
| `SchedulerStalled` | critical | A task last succeeded over 15m ago |
| `OutboxBacklogGrowing` | critical | Oldest undelivered event over 30m old |
| `OutboxTerminalFailures` | warning | Events exhausted their retries in the last hour |
| `OutboxParkedOnConfiguration` | warning | Events parked on a disabled integration for 30m |
| `BookingHoldsNotReleased` | critical | Over 50 overdue holds for 15m |
| `APITargetDown` | critical | Scrapes failing for 2m |
| `APIServerErrorRate` | critical | Over 2% 5xx for 10m |
| `APILatencyDegraded` | warning | p95 over 2s on a route for 10m |

`OutboxTerminalFailures` uses `delta()`, not `increase()`: outbox depth is a gauge, and
`increase()` assumes counter semantics, so it would read a drained queue as a reset.
