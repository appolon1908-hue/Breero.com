# BREERO third-party API

A scoped, key-authenticated surface for integrators. Disabled by default and
release-gated: `THIRD_PARTY_API_ENABLED` is off, production refuses to boot with it on,
and the routes are not registered at all while it is off — a disabled environment
exposes no partner surface to probe, not even a 403.

## Why a separate credential

An integrator is not a person. It has no password, no session, no refresh and no
portal access, and it must never be resolvable through the interactive auth path. So
`ApiClient` is its own entity rather than a `User`, and `app/domains/partner_api/dependencies.py`
is a separate dependency chain from `app/domains/auth/dependencies.py`.

## Keys

Presented as `Authorization: Bearer brk_<prefix>.<secret>`.

- **The secret is never stored.** `api_keys` holds a SHA-256 digest and the public
  prefix. A dump of that table yields nothing usable.
- **Returned exactly once**, from the issue response. `ApiKeyRead` has no `secret`
  field, so no listing can leak one.
- **Expiry is mandatory**, bounded to 365 days.
- **Revocable**, and revocation is immediate — checked on every authentication.
- **Rate-limited per key**, keyed by prefix rather than caller address: an integrator
  behind a NAT or a serverless platform has no stable address, and the credential is
  what should be budgeted.

Every rejection returns the same status and message. A caller must not be able to tell
an unknown key from a revoked, expired or suspended one — that difference is an oracle
for probing which keys exist.

## Scopes

Least privilege, granted explicitly per key.

| Scope | Grants |
| --- | --- |
| `catalog:read` | Read bookable services |
| `coverage:read` | Check whether an address is served |
| `service_request:write` | Submit a service request |
| `service_request:read` | Read back its own requests |
| `webhook:manage` | Manage its own delivery endpoints |

A missing scope returns **403, not 401**: the credential is valid, the grant is not,
and retrying with the same key will never help.

## What a partner cannot see

No provider candidates, no capacity, no worker identities, no pricing internals, no
other integrator's data. The only write is submitting a service request, which enters
manual dispatch and **promises no appointment** — the response says so, and returns 202
rather than 201 so nothing infers a booking.

Requests are scoped by a namespaced idempotency key, `partner:{client_id}:{key}`,
built by the server from the authenticated client. Two integrators cannot collide on
the same key, and neither can read the other's request by guessing an identifier — a
cross-client read returns 404, not 403, so an identifier cannot be confirmed.

## Webhooks

Registered per client over HTTPS only; plaintext would expose both the payload and the
signature.

Deliveries go through the existing durable outbox rather than being attempted inline.
The outbox already owns leasing, retry with backoff, terminal classification and
operator retry — and a third-party endpoint is exactly the dependency that must never
be able to slow down or fail the request that produced the event.

Each delivery carries:

```
X-Breero-Timestamp: 1756713600
X-Breero-Signature: sha256=<hmac>
```

The signature covers `timestamp + "." + body`, so a captured delivery cannot be
replayed later against a receiver that enforces a freshness window. Recompute over the
canonical body — JSON with sorted keys and no whitespace — using the subscription
secret returned once at registration.

Event types: `service_request.received`, `service_request.dispatched`,
`service_request.completed`, `service_request.cancelled`. Anything else is rejected at
registration rather than silently never delivered.

## Operating it

Client, key and webhook administration lives at `/api/v1/admin/partner-api/*` and
requires an authenticated operator with `admin.access.manage`. Nothing there is
reachable with an API key: issuing integrator credentials is an administrative act.

Issuing and revoking a key both write audit rows recording the client, prefix and
scope set — never the secret. An audit row must never be somewhere a credential can be
recovered from.

## Enabling it

Not in this release. `THIRD_PARTY_API_ENABLED` sits alongside payments and the
marketplace flags in `Settings.validate_production`, so production raises on boot if it
is set. Turning it on needs its own certification: the rate limits sized against real
integrator traffic, the webhook delivery path exercised against a real receiver, and
the scope model reviewed against what integrators actually need.
