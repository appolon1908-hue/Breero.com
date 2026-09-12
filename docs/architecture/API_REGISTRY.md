# API registry

The executable contract is `apps/api/openapi.json` at SHA-256 `93748567a1121ee3d8312d08e5d19ea4a81b14e0184e03d0f0eeaba957384ba4`. At this baseline it contains 96 paths and 116 HTTP operations. The application mounts V1 at `/api/v1`, additive V2 at `/api/v2`, internal Odoo routes, and health routes.

## Registered route families

| Version | Path family | Domain/owner | Audience | Mount policy |
|---|---|---|---|---|
| platform | `/health`, `/health/live`, `/health/ready` | runtime | probes/operators | always |
| internal | `/internal/v1/integrations/odoo/*` | integration | trusted service only | always in source; production reachability must be proven |
| V1 | `/api/v1/public/*` | capabilities | public | always |
| V1 | `/api/v1/auth/*` | auth/provider registration/access | public/user/admin | always |
| V1 | `/api/v1/admin/users/*` | identity/RBAC | admin | always |
| V1 | `/api/v1/admin/service-zones/*`, `/admin/postal-codes/*` | geography | admin | always |
| V1 | `/api/v1/admin/provider-applications/*` | provider onboarding | admin | always |
| V1 | `/api/v1/provider/*` | provider onboarding/catalog | provider | always except paid-lead routes |
| V1 | `/api/v1/services/*` | catalog | public/admin | always |
| V1 | `/api/v1/customer/*` | customer resources | customer | always except payments |
| V1 | `/api/v1/privacy-requests*`, `/communications/*` | compliance/privacy/consent | mixed public and authenticated audiences | always; authorization is operation-specific |
| V1 | `/api/v1/addresses/*`, `/booking/address/*`, `/booking/service-area/*`, `/booking/timezone/*` | geography | public/customer | only when geocoding enabled |
| V1 | `/api/v1/availability/*`, `/bookings/*`, `/booking/intents/*` | scheduling/booking | public/customer | only when scheduling enabled |
| V1 | `/api/v1/payments/*`, `/customer/payments/*` | payments | customer/provider callback | payments and Stripe enabled |
| V1 | `/api/v1/jobs/*` | jobs | worker/operations | always |
| V1 | `/api/v1/vendors/*` | workforce | provider/operations | always |
| V1 | `/api/v1/operations/*` | dispatch/matching | operations | always |
| V1 | `/api/v1/finance/*` | finance | finance/admin | payout enabled |
| V1 | `/api/v1/integrations/*` | integrations | operations/admin | always |
| V1 | `/api/v1/service-requests`, `/contact`, `/provider-interest` | public submissions | public | always |
| V1 | `/api/v1/provider/leads/*` | professional leads | provider | paid leads, payments and Stripe enabled |
| V2 | `/api/v2/capabilities` | capabilities | public | always |

## Governance completeness

OpenAPI is the exhaustive endpoint-level registry for method, path, operation ID, tags, schemas, authentication declarations and responses. The repository does not yet maintain all Milestone 3 metadata per operation: business owner, permission, tenant scope, record policy, capability, rate-limit class, idempotency/hash policy, optimistic version policy, PII class, event effect, and deprecation/replacement. Those fields are therefore `UNREGISTERED` rather than inferred. Milestone 3 must introduce a machine-checkable registry and fail CI on drift.

The checked-in OpenAPI is broader than the older `docs/backend-api-inventory.md` statement of 70 paths/77 operations; the checked-in artifact and executable router source take precedence. Conditional route mounting also means a runtime contract varies by capability configuration. Milestone 3 must produce and compare contracts for the approved capability snapshot.

## Frontend contract state

`packages/types` and `packages/api-client` are the intended shared frontend contract surface. `scripts/check-frontend-openapi.mjs` and the root `contract:check` command provide a partial drift check, but the client is handwritten rather than fully generated from OpenAPI. The public/customer app uses shared contracts and BFF routes. The partner, operations, and admin applications instead use `packages/portal`, whose request helper performs direct handwritten API fetches without depending on `packages/types` or `packages/api-client`; their routes are not covered by the current OpenAPI checker. Unknown-route and complete operation-coverage enforcement therefore remain PARTIAL.
