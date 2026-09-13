# Unhandled outbox events

An event without a registered worker handler now becomes `FAILED_TERMINAL` with
error code `UNHANDLED_EVENT_TYPE` on its first delivery attempt. It is not marked
`DELIVERED`, sent to a guessed destination, or repeatedly retried automatically.
Its payload and identity remain stored for investigation and authorized replay.
The diagnostic contains neither the payload nor the event type.

Existing email event handlers and Middleware dispatch retain their behavior.
This change does not certify those transports, enable delivery, or claim that a
Middleware queue acknowledgment proves an Odoo projection was applied. Existing
delivery kill-switch and lease-finalization gaps remain separate release blockers.

## Operations and recovery

Use the existing failed-event surface and terminal-failure metrics to find
`UNHANDLED_EVENT_TYPE`. Review the producer, event schema, tenant/record scope and
intended consumer. Install and independently review the appropriate handler and
its idempotency/reconciliation behavior before replay. Do not turn a missing
handler into a generic success acknowledgment or forward arbitrary payloads.

Use the existing authorized integration retry path after staging validation. It
records `integration.retry` with the actor and preserves the event identity.
Retrying before a handler exists fails terminally again. Previously misclassified
delivered events are not rewritten by this PR: reconcile them with external
evidence before a separately reviewed data repair, to avoid duplicate effects.

The worker task result remains the number of processed attempts, including
failures; it is not a delivery count. Assess per-event status and terminal-failure
metrics. `processed_at` may record a terminal attempt, not successful delivery.

## Verification and rollback

Unit tests prove unknown events never invoke a transport and existing notification
and Middleware dispatch still work. An isolated PostgreSQL test verifies durable
terminal status, retained payload, cleared lease and audited explicit replay to a
test handler. The full backend suite and deterministic OpenAPI checks also run.

No migration or capability activation is included. A code rollback removes this
guard, so pause processing of unhandled types until equivalent enforcement is
restored. Preserve failed records and event IDs. No deployment is performed by
this implementation PR.
