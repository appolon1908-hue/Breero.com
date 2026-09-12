# Capability registry

Source of truth: defaults in `apps/api/app/config.py` at baseline SHA. Environment overrides are deployment state and require separate evidence.

| Product capability | Source setting | Default | Classification |
|---|---|---:|---|
| Stripe adapter | `STRIPE_ENABLED` | false | DARK |
| Customer payments | `PAYMENTS_ENABLED` | false | DARK |
| Online checkout | `ONLINE_CHECKOUT_ENABLED` | false | DARK |
| Paid leads | `PAID_LEADS_ENABLED` | false | DARK |
| Automatic refunds | `AUTOMATIC_REFUNDS_ENABLED` | false | DARK |
| Automatic booking | `AUTOMATIC_BOOKING_ENABLED` | false | DARK |
| Scheduling | `SCHEDULING_ENABLED` | true | COMPLETE for current slice |
| Automatic provider assignment | `AUTOMATIC_PROVIDER_ASSIGNMENT_ENABLED` | false | DARK |
| Automatic confirmation | `AUTOMATIC_CONFIRMED_BOOKINGS` | false | DARK |
| Provider self-service | `PROVIDER_SELF_SERVICE_ENABLED` | false | DARK |
| Marketplace matching | `MARKETPLACE_MATCHING_ENABLED` | false | DARK |
| Messaging | `MARKETPLACE_MESSAGING_ENABLED` | false | STUB/DARK |
| Reviews | `MARKETPLACE_REVIEWS_ENABLED` | false | STUB/DARK |
| Payouts | `PAYOUT_ENABLED` | false | DARK |
| Marketing email | `MARKETING_EMAIL_ENABLED` | false | DARK |
| Marketing SMS | `MARKETING_SMS_ENABLED` | false | DARK |
| Keycloak validation | `KEYCLOAK_ENABLED` | false | PARTIAL/DARK |
| Geocoding/address APIs | `GEOCODING_ENABLED` | false | DARK |
| Middleware delivery | `MIDDLEWARE_ENABLED` | false | DARK |
| Direct Odoo | `ODOO_ENABLED` | false | DEPRECATED/forbidden in production |
| Legacy SMTP email | `EMAIL_ENABLED` | false | DEPRECATED for platform target |
| Legacy SMS provider | `SMS_ENABLED` | false | DEPRECATED for platform target |
| API metrics setting | `METRICS_ENABLED` | true | STUB; setting is not full exposition |
| Transactional email | `TRANSACTIONAL_EMAIL_MODE` | `controlled_canary` | DARK pending Klyrow certification |
| Transactional SMS | `TRANSACTIONAL_SMS_MODE` | `controlled_canary` | DARK pending Telnexa certification |

The mission-standard aliases `PAYOUTS_ENABLED`, `AUTO_ASSIGN_PROVIDER`, `AUTO_CONFIRM_BOOKING`, `MESSAGING_ENABLED`, `REVIEWS_ENABLED`, `LIVE_EMAIL_DELIVERY`, `LIVE_SMS_DELIVERY`, `FEATURED_PROVIDERS_ENABLED`, `MARKETING_ENABLED`, and `AI_AUTOMATION_ENABLED` do not all exist under those exact names. Until normalized and certified, absence means disabled; it must never be interpreted as enabled.

Implementation and activation require separate pull requests. This registry records source defaults only and authorizes no deployment change.
