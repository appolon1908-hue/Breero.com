# BREERO Marketplace V2 — Accepted Baseline and Activation Status

## Authority and date

Current-state status authority as of **2026-08-26**.

This document corrects status-only language in earlier Marketplace V2 drafts that described the accepted application as request-only. It does not replace domain, security, system-of-record, API, event, retention or release-control requirements elsewhere in the package.

When another document describes current implementation or activation status differently, this file controls until an exact-head reviewed update replaces it.

## Accepted application baseline

```text
ACCEPTED_MAIN_SHA=8071572c90905d98894ab1a4cafe99a4178f7dd8
PR_34=MERGED
PR_34_ACCEPTED_HEAD=b3de8e1d025e87540fcf2f38f973ab076a282722
PR_35=CONTAINED_IN_ACCEPTED_MAIN
ALEMBIC_HEAD=017_provider_credentials
```

The accepted release boundary is:

```text
request intake
quote-only workflow
operator-confirmed manual scheduling
payment-disabled behavior
fail-closed high-risk capabilities
```

It is not merely the older request-only baseline.

## Current implementation status

```text
QUOTE_ONLY_MANUAL_SCHEDULING_BASELINE=ACCEPTED_IN_MAIN
MARKETPLACE_V2=NO_GO
P0_API_FOUNDATION=READY_FOR_INDEPENDENT_REVIEW
P0_AUTHENTICATION=NOT_STARTED_FROM_ACCEPTED_P0_MERGE
P0_AUTHORIZATION=NOT_STARTED_FROM_ACCEPTED_P0_MERGE
P0_FINAL=FAIL
PRODUCTION_READY=NO
PRODUCTION_DEPLOYED=NO
CAPABILITIES_ACTIVATED=NO
```

PR #38 is the current P0 API-foundation implementation review candidate. Its exact-head CI success is evidence for that PR only; it does not mean P0 final, Marketplace V2, production readiness, or capability activation passed.

## Current disabled capabilities

```text
payments=false
payouts=false
paid_leads=false
instant_booking=false
automatic_booking=false
automatic_assignment=false
automatic_confirmation=false
provider_self_service=false
marketplace_matching=false
messaging=false
reviews=false
marketing=false
unrestricted_email=false
unrestricted_sms=false
external_automation=false
```

Manual scheduling routes already accepted by PR #34 may remain present. They do not imply any automatic or financial capability.

## Current active review sequence

```text
1. independently review unchanged PR #38 exact head
2. merge only after required approval, resolved threads and unambiguous required checks
3. verify the new main SHA and exact checks
4. implement production authentication/identity
5. implement authorization/tenant/record policy
6. continue remaining P0 foundations in dependency order
7. begin marketplace domains only after P0_FINAL=PASS
```

The next engineering boundary is production identity/authentication and authorization. Provider, matching, opportunity, messaging, reviews, financial transactions and activation work must not begin early.

## Current operational and governance blockers

Fresh evidence remains required for:

```text
#17 production-host disk/capacity safety
#18 isolated staging/UAT/DNS/provider readiness
#19 public data-plane ports and production database revision
#45 required-check/ruleset governance
```

Observations recorded on 2026-08-12 are historical until revalidated read-only on the actual approved infrastructure.

## Non-authority

This status record does not:

```text
merge a pull request
deploy an image
migrate production data
change DNS/proxy/firewall/ports
write secrets
activate an integration
send email or SMS
charge or transfer money
assign or confirm work automatically
enable a Marketplace V2 capability
```

Any status change requires exact release identity, current evidence and the reviews/approvals defined by `07_PRODUCTION_READINESS_GATES.md`.
