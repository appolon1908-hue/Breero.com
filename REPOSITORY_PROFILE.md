# Repository Profile — `Breero.com`

## Identity

- **Repository:** `appolon1908-hue/Breero.com`
- **Category:** Product platform — home-services marketplace
- **Visibility:** `public`
- **Default branch:** `main`
- **Authority:** Primary full-stack BREERO marketplace and field-service orchestration authority
- **Status:** Active monorepo containing API, public marketplace, partner, operations, administration, shared packages, infrastructure, and documentation.

## Purpose

Runs BREERO’s home-services marketplace from service discovery and booking through pricing, payments, vendor matching, dispatch, field work, finance, and operations.

## Owns

- FastAPI marketplace backend and PostgreSQL/PostGIS state
- Customer, partner, technician, operations, and admin applications
- Booking, quote, pricing, payment, job, dispatch, document, and marketplace workflows

## Does not own

- Shared Codestra identity, gateway, or cross-system write authority
- Direct provider credentials in browser applications
- Production payment/provider effects before capability and release gates pass

## Key integrations

- Keycloak, Kong, and Middleware
- Stripe and approved payment adapters
- Maps/geocoding, communications, Odoo, and n8n through governed boundaries

## Current priorities

1. Finish identity, tenancy, authorization, idempotency, concurrency, outbox, and inbox foundations
2. Complete quote versioning, jobs, dispatch, payments, documents, and PostGIS workflows
3. Align every frontend with generated API contracts
4. Prove staging, rollback, security, and immutable release evidence

## Governance and safety

- Target promotion model: `feature/docs/fix/security/upgrade -> development -> test -> staging -> production -> main`.
- Use pull requests and exact-head/merge-result validation; merging source never authorizes deployment.
- Never commit secrets, credentials, private keys, customer data, database dumps, or secret-bearing evidence.
- Production images and releases must be immutable; mutable `latest` tags are not release authority.
- External payments, messages, provisioning, and business mutations remain capability-gated until separately approved.
- This document does not deploy software or activate production.

## Account-wide catalog

See `appolon1908-hue/documentaions/REPOSITORY_CATALOG.md`.
