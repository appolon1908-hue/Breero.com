# Horizon portfolio-shell adoption

## Authority

- Horizon repository: `appolon1908-hue/SDK-repository`
- Foundation PR: `#73`
- Foundation exact head: `7db4c6549a0a007922355090f03c082a308f3855`
- Adoption branch: `feature/horizon-portfolio-shell-v1`
- Product theme: `breero`
- Runtime activation: **not included**

`apps/web/app/horizon.css` is a generated adapter pinned to the foundation exact head. It is temporary until the shared `@codestra/intake-ui` package is released and can be consumed at an exact version.

## Canonical domains

| Role | Domain |
|---|---|
| Public marketplace | `https://breero.com` |
| Partner portal | `https://partners.breero.com` |
| Operations portal | `https://ops.breero.com` |
| Administration portal | `https://admin.breero.com` |
| Corporate authority | `https://codestra.co` |
| Canonical identity issuer | `https://auth.codestra.co/realms/codestra` |

Public, partner, operations, administration, identity and API domains are separate trust boundaries. A public header may link to another surface, but it must not treat an operator, identity or API host as a public marketing route.

## Authentication and session rule

Breero has real account logic; the shared shell is connected to it rather than showing decorative authentication buttons.

- Keycloak mode uses Authorization Code Flow with PKCE S256.
- The fallback customer API mode uses the canonical `/auth/login`, refresh and `/auth/logout` operations.
- The public header reads the real customer session and displays either **Sign in** or **Account + Log out**.
- Protected `/account` pages fail closed through `AccountFrame` before the account shell renders.
- Logout attempts provider/API revocation, always clears Breero credentials locally, and never calls `sessionStorage.clear()`.
- Expired JWT access tokens are removed before a page is treated as authenticated.
- Post-login destinations are restricted to same-origin paths to prevent open redirects.
- Backend authorization remains authoritative for every protected read and command.
- The target durable identity is Keycloak `issuer + subject`; the current API-session compatibility path is migration-required.
- Public-only surfaces must hide login/logout controls unless a real session implementation exists.

Authoritative implementation files:

- `apps/web/components/account/auth-form.tsx`
- `apps/web/app/account/callback/page.tsx`
- `apps/web/lib/keycloak.ts`
- `apps/web/lib/customer/session-actions.ts`
- `apps/web/components/account/account-frame.tsx`
- `apps/web/components/account/account-nav.tsx`
- `apps/web/components/site-header.tsx`

## Page and color rule

Every Breero page is wrapped by `apps/web/app/layout.tsx` and `AppShell`. New pages must therefore inherit:

- `data-horizon-root`
- `data-horizon-theme="breero"`
- the shared header and footer
- the same typography, spacing, focus, form, card, table and CTA hierarchy
- applicable loading, empty, partial, stale, error, unauthorized, offline and durable-success states

New page and component files must not introduce raw product colors. Use Horizon variables such as `var(--hz-bg)`, `var(--hz-text)`, `var(--hz-accent)`, `var(--hz-border)`, `var(--hz-success)`, `var(--hz-warning)` and `var(--hz-danger)`. Raw color definitions belong only in the registered token adapter.

## New suite rule

A new Breero application or portal cannot be added only as a directory. Before merge it must register:

1. its canonical HTTPS domain and surface type;
2. its Horizon theme and root layout;
3. its header/footer or approved operator-shell equivalent;
4. its real login, session, route-guard and logout implementation when it has protected routes;
5. its Keycloak client, issuer, scopes, audience and allowed roles;
6. backend-authoritative permission and record-level authorization;
7. its page-state, accessibility, build, test and rollback evidence.

The validator must reject unregistered suites, fake login/logout controls, missing root-shell markers, missing auth source files and newly added raw colors outside the registered token file.

## Preserved behavior

- booking CTA and analytics attributes
- account and booking routes
- existing marketing navigation
- mobile Escape-key handling
- service, legal, privacy, consent and professional links
- legal identity and no-online-payment disclosure
- Next.js metadata and current brand assets

## Validation

```bash
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm --filter @breero/web test:e2e
```

No marketplace provider, payment, DNS, deployment, secret or production-runtime behavior is enabled by this branch.
