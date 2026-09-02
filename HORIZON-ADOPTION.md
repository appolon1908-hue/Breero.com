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

The public marketplace header keeps the existing booking and account routes. Operator and administration domains are visible in the domain registry/footer but are not treated as public booking routes.

## Preserved behavior

- booking CTA and analytics attributes
- account route
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

No marketplace API, authentication, payments, provider workflow, DNS, deployment or production-runtime behavior is changed by this branch.
