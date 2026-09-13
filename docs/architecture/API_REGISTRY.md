# API registry

[Machine inventory](SOURCE_INVENTORY.json) provides endpoint-level evidence in `api_operations`, with membership lists under `runtime_profiles`. Source baseline is `c8b5d31df80cd715ae189db9e16d6ff082c0d51f`. The default executable OpenAPI exactly equals [apps/api/openapi.json](../../apps/api/openapi.json), whose SHA-256 is `93748567a1121ee3d8312d08e5d19ea4a81b14e0184e03d0f0eeaba957384ba4`.

| Profile | OpenAPI paths | OpenAPI operations | Hidden application operations |
|---|---:|---:|---|
| Default source flags | 96 | 116 | `GET /metrics` |
| Implemented route families imported in isolated test configuration | 118 | 138 | `GET /metrics` |

The second profile mounts geocoding, Stripe/payments, payouts and paid-lead families for inventory only. It does not start servers, dispatch requests or activate any deployment capability. Framework routes `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, and `/redoc` are also mounted; GET/HEAD methods are separately recorded in `framework_routes`. Metrics and framework documentation are outside OpenAPI.

## Governance status

Every application operation below has method/path/version, Python module/handler/source, OpenAPI authentication declarations, dependency callable names, declared allowed roles or permissions when available, request/parameter/response schemas and documented errors in the machine inventory. `domain` is the actual Python handler module, not an invented business ownership assignment. Body-level policies, tenant/record checks, capability enforcement and atomic effects cannot be proven from OpenAPI alone.

The remaining Milestone 3 fields (`owner`, `audience`, `permission`, `tenant_scope`, `record_policy`, `capability`, `rate_limit_class`, `idempotency_requirement`, `request_hash_policy`, `optimistic_version_policy`, `PII_classification`, `event_effect`, `deprecation_state`, `replacement_endpoint`) are explicitly `UNREGISTERED` per operation. This is an inventory of the governance gap, not a claim that these protections are absent in every handler or that a full authorization registry exists. Do not use UNREGISTERED metadata to allow traffic or infer public access. Milestone 3 must review service-level effects and make the registry enforceable in CI.

In particular, the jobs family includes customer work-request decisions; integrations permits finance/admin; internal Odoo read/retry handlers permit operations/finance/admin. The internal route prefix is `/internal/v1/integrations/odoo`, and compliance is mounted at `/api/v1/privacy-requests*` and `/api/v1/communications/*` with mixed audiences. Dependency metadata records effective access-role sets, which can include mapped roles beyond legacy role names.

## Frontend contracts and CI

The shared `packages/types` and `packages/api-client` contracts are handwritten. `node scripts/check-frontend-openapi.mjs` passes for 30 required paths, selected enum values and absence of payment mutations in the default artifact. It does not enumerate arbitrary frontend calls or prove schema-wide type parity. `packages/portal/src/index.tsx` performs direct handwritten fetches and is not covered by that checker. PR #115 proposes generated contracts on top of PR #109; neither is accepted baseline code.

Backend CI generates OpenAPI and checks it is nonempty, but currently lacks a post-generation Git diff equality gate. The inventory checker proves exact default semantic equality for this baseline. It is not a replacement for the planned permanent OpenAPI/typed-client/policy drift gates.

## Every implemented application operation

`Default` means present with source defaults, not public or authorized. The full dependency and schema evidence is in the machine inventory. Operations excluded from the default profile require separate reviewed activation.

| Method | Path | Default | Handler source |
|---|---|---|---|
| POST | `/api/v1/addresses/validate` | no | [apps/api/app/api/v1/addresses.py](../../apps/api/app/api/v1/addresses.py) (`validate_address`) |
| GET | `/api/v1/admin/postal-codes` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`list_postal_codes`) |
| POST | `/api/v1/admin/postal-codes` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`create_postal_code`) |
| POST | `/api/v1/admin/postal-codes/import` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`import_postal_codes`) |
| GET | `/api/v1/admin/postal-codes/imports/{import_id}` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`get_postal_code_import`) |
| DELETE | `/api/v1/admin/postal-codes/{postal_code_id}` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`deactivate_postal_code`) |
| PATCH | `/api/v1/admin/postal-codes/{postal_code_id}` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`update_postal_code`) |
| GET | `/api/v1/admin/provider-applications` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`list_provider_applications`) |
| GET | `/api/v1/admin/provider-applications/{application_id}` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`get_provider_application`) |
| POST | `/api/v1/admin/provider-applications/{application_id}/approve` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`approve_provider_application`) |
| POST | `/api/v1/admin/provider-applications/{application_id}/reject` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`reject_provider_application`) |
| POST | `/api/v1/admin/provider-applications/{application_id}/request-information` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`request_provider_information`) |
| GET | `/api/v1/admin/service-zones` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`list_service_zones`) |
| POST | `/api/v1/admin/service-zones` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`create_service_zone`) |
| DELETE | `/api/v1/admin/service-zones/{service_area_id}` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`deactivate_service_zone`) |
| GET | `/api/v1/admin/service-zones/{service_area_id}` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`get_service_zone`) |
| PATCH | `/api/v1/admin/service-zones/{service_area_id}` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`update_service_zone`) |
| GET | `/api/v1/admin/service-zones/{service_area_id}/coverage` | yes | [apps/api/app/api/v1/admin_geography.py](../../apps/api/app/api/v1/admin_geography.py) (`get_service_zone_coverage`) |
| POST | `/api/v1/admin/users` | yes | [apps/api/app/api/v1/admin_users.py](../../apps/api/app/api/v1/admin_users.py) (`provision_internal_user`) |
| GET | `/api/v1/auth/access/catalog` | yes | [apps/api/app/api/v1/access.py](../../apps/api/app/api/v1/access.py) (`access_catalog`) |
| GET | `/api/v1/auth/access/users/{user_id}` | yes | [apps/api/app/api/v1/access.py](../../apps/api/app/api/v1/access.py) (`user_access`) |
| PUT | `/api/v1/auth/access/users/{user_id}` | yes | [apps/api/app/api/v1/access.py](../../apps/api/app/api/v1/access.py) (`replace_user_access`) |
| GET | `/api/v1/auth/context` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`portal_context`) |
| POST | `/api/v1/auth/email/resend` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`resend`) |
| POST | `/api/v1/auth/email/resend-verification` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`resend`) |
| POST | `/api/v1/auth/email/verify` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`verify`) |
| POST | `/api/v1/auth/login` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`login`) |
| GET | `/api/v1/auth/login-mode` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`login_mode`) |
| POST | `/api/v1/auth/logout` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`logout`) |
| POST | `/api/v1/auth/logout-all` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`logout_all`) |
| GET | `/api/v1/auth/me` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`me`) |
| POST | `/api/v1/auth/password/change` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`change`) |
| POST | `/api/v1/auth/password/forgot` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`forgot`) |
| POST | `/api/v1/auth/password/reset` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`reset`) |
| POST | `/api/v1/auth/password/set` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`set_initial_password`) |
| POST | `/api/v1/auth/refresh` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`refresh`) |
| POST | `/api/v1/auth/register` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`register`) |
| POST | `/api/v1/auth/register/client` | yes | [apps/api/app/api/v1/auth.py](../../apps/api/app/api/v1/auth.py) (`register`) |
| POST | `/api/v1/auth/register/provider` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`register_provider`) |
| POST | `/api/v1/availability/search` | yes | [apps/api/app/api/v1/availability.py](../../apps/api/app/api/v1/availability.py) (`search_availability`) |
| POST | `/api/v1/booking/address/validate` | no | [apps/api/app/api/v1/booking_geography.py](../../apps/api/app/api/v1/booking_geography.py) (`validate_booking_address`) |
| POST | `/api/v1/booking/intents` | yes | [apps/api/app/api/v1/booking_intents.py](../../apps/api/app/api/v1/booking_intents.py) (`create_booking_intent`) |
| DELETE | `/api/v1/booking/intents/{intent_id}` | yes | [apps/api/app/api/v1/booking_intents.py](../../apps/api/app/api/v1/booking_intents.py) (`abandon_booking_intent`) |
| GET | `/api/v1/booking/intents/{intent_id}` | yes | [apps/api/app/api/v1/booking_intents.py](../../apps/api/app/api/v1/booking_intents.py) (`get_booking_intent`) |
| PATCH | `/api/v1/booking/intents/{intent_id}` | yes | [apps/api/app/api/v1/booking_intents.py](../../apps/api/app/api/v1/booking_intents.py) (`update_booking_intent`) |
| POST | `/api/v1/booking/intents/{intent_id}/submit` | yes | [apps/api/app/api/v1/booking_intents.py](../../apps/api/app/api/v1/booking_intents.py) (`submit_booking_intent`) |
| POST | `/api/v1/booking/service-area/check` | no | [apps/api/app/api/v1/booking_geography.py](../../apps/api/app/api/v1/booking_geography.py) (`check_booking_service_area`) |
| POST | `/api/v1/booking/timezone/resolve` | no | [apps/api/app/api/v1/booking_geography.py](../../apps/api/app/api/v1/booking_geography.py) (`resolve_booking_timezone`) |
| POST | `/api/v1/bookings` | yes | [apps/api/app/api/v1/bookings.py](../../apps/api/app/api/v1/bookings.py) (`create_booking`) |
| GET | `/api/v1/bookings/{booking_id}/confirmation` | yes | [apps/api/app/api/v1/bookings.py](../../apps/api/app/api/v1/bookings.py) (`booking_confirmation`) |
| POST | `/api/v1/communications/preferences` | yes | [apps/api/app/api/v1/compliance.py](../../apps/api/app/api/v1/compliance.py) (`preferences`) |
| POST | `/api/v1/communications/sms-revocations` | yes | [apps/api/app/api/v1/compliance.py](../../apps/api/app/api/v1/compliance.py) (`sms_revocation`) |
| POST | `/api/v1/contact` | yes | [apps/api/app/api/v1/public_forms.py](../../apps/api/app/api/v1/public_forms.py) (`contact`) |
| GET | `/api/v1/customer/addresses` | yes | [apps/api/app/api/v1/customer/addresses.py](../../apps/api/app/api/v1/customer/addresses.py) (`addresses`) |
| POST | `/api/v1/customer/addresses` | yes | [apps/api/app/api/v1/customer/addresses.py](../../apps/api/app/api/v1/customer/addresses.py) (`add_address`) |
| DELETE | `/api/v1/customer/addresses/{address_id}` | yes | [apps/api/app/api/v1/customer/addresses.py](../../apps/api/app/api/v1/customer/addresses.py) (`delete_address`) |
| PATCH | `/api/v1/customer/addresses/{address_id}` | yes | [apps/api/app/api/v1/customer/addresses.py](../../apps/api/app/api/v1/customer/addresses.py) (`update_address`) |
| GET | `/api/v1/customer/bookings` | yes | [apps/api/app/api/v1/customer/bookings.py](../../apps/api/app/api/v1/customer/bookings.py) (`bookings`) |
| GET | `/api/v1/customer/bookings/{booking_id}` | yes | [apps/api/app/api/v1/customer/bookings.py](../../apps/api/app/api/v1/customer/bookings.py) (`booking`) |
| POST | `/api/v1/customer/bookings/{booking_id}/cancel` | yes | [apps/api/app/api/v1/customer/bookings.py](../../apps/api/app/api/v1/customer/bookings.py) (`cancel_booking`) |
| GET | `/api/v1/customer/payments` | no | [apps/api/app/api/v1/customer/payments.py](../../apps/api/app/api/v1/customer/payments.py) (`payments`) |
| GET | `/api/v1/customer/payments/{payment_id}` | no | [apps/api/app/api/v1/customer/payments.py](../../apps/api/app/api/v1/customer/payments.py) (`payment`) |
| GET | `/api/v1/customer/profile` | yes | [apps/api/app/api/v1/customer/profile.py](../../apps/api/app/api/v1/customer/profile.py) (`profile`) |
| PATCH | `/api/v1/customer/profile` | yes | [apps/api/app/api/v1/customer/profile.py](../../apps/api/app/api/v1/customer/profile.py) (`update_profile`) |
| GET | `/api/v1/customer/quotes` | yes | [apps/api/app/api/v1/customer/quotes.py](../../apps/api/app/api/v1/customer/quotes.py) (`quotes`) |
| GET | `/api/v1/customer/quotes/{quote_id}` | yes | [apps/api/app/api/v1/customer/quotes.py](../../apps/api/app/api/v1/customer/quotes.py) (`quote`) |
| POST | `/api/v1/customer/quotes/{quote_id}/decision` | yes | [apps/api/app/api/v1/customer/quotes.py](../../apps/api/app/api/v1/customer/quotes.py) (`decide_quote`) |
| POST | `/api/v1/finance/compensation-plans` | no | [apps/api/app/api/v1/finance.py](../../apps/api/app/api/v1/finance.py) (`create_compensation_plan`) |
| GET | `/api/v1/finance/earnings` | no | [apps/api/app/api/v1/finance.py](../../apps/api/app/api/v1/finance.py) (`list_earnings`) |
| POST | `/api/v1/finance/earnings/{earning_id}/adjustments` | no | [apps/api/app/api/v1/finance.py](../../apps/api/app/api/v1/finance.py) (`adjust_earning`) |
| POST | `/api/v1/finance/payout-batches` | no | [apps/api/app/api/v1/finance.py](../../apps/api/app/api/v1/finance.py) (`create_batch`) |
| POST | `/api/v1/finance/payout-batches/{batch_id}/approve` | no | [apps/api/app/api/v1/finance.py](../../apps/api/app/api/v1/finance.py) (`approve_batch`) |
| POST | `/api/v1/finance/payout-batches/{batch_id}/submit` | no | [apps/api/app/api/v1/finance.py](../../apps/api/app/api/v1/finance.py) (`submit_batch`) |
| POST | `/api/v1/integrations/events/{event_id}/retry` | yes | [apps/api/app/api/v1/integrations.py](../../apps/api/app/api/v1/integrations.py) (`retry_event`) |
| GET | `/api/v1/integrations/failures` | yes | [apps/api/app/api/v1/integrations.py](../../apps/api/app/api/v1/integrations.py) (`failures`) |
| GET | `/api/v1/integrations/health` | yes | [apps/api/app/api/v1/integrations.py](../../apps/api/app/api/v1/integrations.py) (`provider_health`) |
| GET | `/api/v1/jobs` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`list_jobs`) |
| POST | `/api/v1/jobs/work-requests/{request_id}/decision` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`decide_work_request`) |
| POST | `/api/v1/jobs/work-requests/{request_id}/review` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`review_work_request`) |
| GET | `/api/v1/jobs/{job_id}` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`get_job`) |
| POST | `/api/v1/jobs/{job_id}/completion` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`complete_with_notes`) |
| POST | `/api/v1/jobs/{job_id}/diagnostic` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`record_diagnostic`) |
| POST | `/api/v1/jobs/{job_id}/technician/{command}` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`technician_command`) |
| POST | `/api/v1/jobs/{job_id}/transition` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`transition_job`) |
| GET | `/api/v1/jobs/{job_id}/work-requests` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`list_work_requests`) |
| POST | `/api/v1/jobs/{job_id}/work-requests` | yes | [apps/api/app/api/v1/jobs.py](../../apps/api/app/api/v1/jobs.py) (`create_work_request`) |
| POST | `/api/v1/operations/bookings/{booking_id}/confirm` | yes | [apps/api/app/api/v1/operations.py](../../apps/api/app/api/v1/operations.py) (`confirm_booking`) |
| GET | `/api/v1/operations/dispatcher/queue` | yes | [apps/api/app/api/v1/operations.py](../../apps/api/app/api/v1/operations.py) (`dispatcher_queue`) |
| PATCH | `/api/v1/operations/dispatcher/queue/{request_id}` | yes | [apps/api/app/api/v1/operations.py](../../apps/api/app/api/v1/operations.py) (`update_dispatcher_queue_item`) |
| POST | `/api/v1/operations/jobs/{job_id}/assign` | yes | [apps/api/app/api/v1/operations.py](../../apps/api/app/api/v1/operations.py) (`assign_job`) |
| POST | `/api/v1/operations/jobs/{job_id}/match` | yes | [apps/api/app/api/v1/operations.py](../../apps/api/app/api/v1/operations.py) (`match_job`) |
| PUT | `/api/v1/operations/vendors/{vendor_id}/credentials/{credential_type}/{jurisdiction}` | yes | [apps/api/app/api/v1/operations.py](../../apps/api/app/api/v1/operations.py) (`upsert_provider_credential`) |
| PATCH | `/api/v1/operations/vendors/{vendor_id}/status` | yes | [apps/api/app/api/v1/operations.py](../../apps/api/app/api/v1/operations.py) (`set_vendor_status`) |
| PUT | `/api/v1/operations/workers/{worker_id}/booking-coverage` | yes | [apps/api/app/api/v1/operations.py](../../apps/api/app/api/v1/operations.py) (`replace_booking_coverage`) |
| POST | `/api/v1/payments/intents` | no | [apps/api/app/api/v1/payments.py](../../apps/api/app/api/v1/payments.py) (`create_intent`) |
| POST | `/api/v1/payments/webhooks/stripe` | no | [apps/api/app/api/v1/payments.py](../../apps/api/app/api/v1/payments.py) (`stripe_webhook`) |
| GET | `/api/v1/payments/{payment_id}` | no | [apps/api/app/api/v1/payments.py](../../apps/api/app/api/v1/payments.py) (`get_payment`) |
| POST | `/api/v1/payments/{payment_id}/capture` | no | [apps/api/app/api/v1/payments.py](../../apps/api/app/api/v1/payments.py) (`capture_payment`) |
| POST | `/api/v1/payments/{payment_id}/refunds` | no | [apps/api/app/api/v1/payments.py](../../apps/api/app/api/v1/payments.py) (`create_refund`) |
| POST | `/api/v1/privacy-requests` | yes | [apps/api/app/api/v1/compliance.py](../../apps/api/app/api/v1/compliance.py) (`create_privacy_request`) |
| GET | `/api/v1/privacy-requests/{request_id}` | yes | [apps/api/app/api/v1/compliance.py](../../apps/api/app/api/v1/compliance.py) (`privacy_request_status`) |
| POST | `/api/v1/provider-interest` | yes | [apps/api/app/api/v1/public_forms.py](../../apps/api/app/api/v1/public_forms.py) (`provider_interest`) |
| GET | `/api/v1/provider/leads` | no | [apps/api/app/api/v1/provider_leads.py](../../apps/api/app/api/v1/provider_leads.py) (`list_leads`) |
| GET | `/api/v1/provider/leads/{lead_id}` | no | [apps/api/app/api/v1/provider_leads.py](../../apps/api/app/api/v1/provider_leads.py) (`get_lead`) |
| POST | `/api/v1/provider/leads/{lead_id}/disputes` | no | [apps/api/app/api/v1/provider_leads.py](../../apps/api/app/api/v1/provider_leads.py) (`create_dispute`) |
| GET | `/api/v1/provider/leads/{lead_id}/disputes/{dispute_id}` | no | [apps/api/app/api/v1/provider_leads.py](../../apps/api/app/api/v1/provider_leads.py) (`get_dispute`) |
| POST | `/api/v1/provider/leads/{lead_id}/purchase` | no | [apps/api/app/api/v1/provider_leads.py](../../apps/api/app/api/v1/provider_leads.py) (`purchase_lead`) |
| GET | `/api/v1/provider/onboarding` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`provider_onboarding`) |
| PATCH | `/api/v1/provider/onboarding` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`update_provider_onboarding`) |
| POST | `/api/v1/provider/onboarding/submit` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`submit_provider_onboarding`) |
| GET | `/api/v1/provider/profile` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`provider_profile`) |
| PATCH | `/api/v1/provider/profile` | yes | [apps/api/app/api/v1/provider_onboarding.py](../../apps/api/app/api/v1/provider_onboarding.py) (`update_provider_profile`) |
| GET | `/api/v1/provider/services` | yes | [apps/api/app/api/v1/provider_catalog.py](../../apps/api/app/api/v1/provider_catalog.py) (`list_provider_services`) |
| POST | `/api/v1/provider/services` | yes | [apps/api/app/api/v1/provider_catalog.py](../../apps/api/app/api/v1/provider_catalog.py) (`add_provider_service`) |
| DELETE | `/api/v1/provider/services/{provider_service_id}` | yes | [apps/api/app/api/v1/provider_catalog.py](../../apps/api/app/api/v1/provider_catalog.py) (`remove_provider_service`) |
| PATCH | `/api/v1/provider/services/{provider_service_id}` | yes | [apps/api/app/api/v1/provider_catalog.py](../../apps/api/app/api/v1/provider_catalog.py) (`update_provider_service`) |
| GET | `/api/v1/provider/skills` | yes | [apps/api/app/api/v1/provider_catalog.py](../../apps/api/app/api/v1/provider_catalog.py) (`list_provider_skills`) |
| POST | `/api/v1/provider/skills` | yes | [apps/api/app/api/v1/provider_catalog.py](../../apps/api/app/api/v1/provider_catalog.py) (`add_provider_skill`) |
| DELETE | `/api/v1/provider/skills/{provider_skill_id}` | yes | [apps/api/app/api/v1/provider_catalog.py](../../apps/api/app/api/v1/provider_catalog.py) (`remove_provider_skill`) |
| GET | `/api/v1/public/capabilities` | yes | [apps/api/app/api/v1/capabilities.py](../../apps/api/app/api/v1/capabilities.py) (`capabilities`) |
| POST | `/api/v1/service-requests` | yes | [apps/api/app/api/v1/public_forms.py](../../apps/api/app/api/v1/public_forms.py) (`service_request`) |
| GET | `/api/v1/services` | yes | [apps/api/app/api/v1/services.py](../../apps/api/app/api/v1/services.py) (`list_services`) |
| POST | `/api/v1/services` | yes | [apps/api/app/api/v1/services.py](../../apps/api/app/api/v1/services.py) (`create_service`) |
| GET | `/api/v1/services/{service_id}` | yes | [apps/api/app/api/v1/services.py](../../apps/api/app/api/v1/services.py) (`get_service`) |
| GET | `/api/v1/services/{service_id}/questions` | yes | [apps/api/app/api/v1/services.py](../../apps/api/app/api/v1/services.py) (`list_service_questions`) |
| GET | `/api/v1/vendors` | yes | [apps/api/app/api/v1/vendors.py](../../apps/api/app/api/v1/vendors.py) (`list_vendors`) |
| POST | `/api/v1/vendors` | yes | [apps/api/app/api/v1/vendors.py](../../apps/api/app/api/v1/vendors.py) (`create_vendor`) |
| POST | `/api/v1/vendors/{vendor_id}/offers/{offer_id}/decision` | yes | [apps/api/app/api/v1/vendors.py](../../apps/api/app/api/v1/vendors.py) (`decide_offer`) |
| GET | `/api/v1/vendors/{vendor_id}/workers` | yes | [apps/api/app/api/v1/vendors.py](../../apps/api/app/api/v1/vendors.py) (`list_workers`) |
| POST | `/api/v1/vendors/{vendor_id}/workers` | yes | [apps/api/app/api/v1/vendors.py](../../apps/api/app/api/v1/vendors.py) (`create_worker`) |
| GET | `/api/v2/capabilities` | yes | [apps/api/app/api/v2/capabilities.py](../../apps/api/app/api/v2/capabilities.py) (`capabilities`) |
| GET | `/health` | yes | [apps/api/app/main.py](../../apps/api/app/main.py) (`health`) |
| GET | `/health/live` | yes | [apps/api/app/main.py](../../apps/api/app/main.py) (`live`) |
| GET | `/health/ready` | yes | [apps/api/app/main.py](../../apps/api/app/main.py) (`ready`) |
| GET | `/internal/v1/integrations/odoo/deliveries/{event_id}` | yes | [apps/api/app/api/internal_odoo.py](../../apps/api/app/api/internal_odoo.py) (`delivery`) |
| POST | `/internal/v1/integrations/odoo/deliveries/{event_id}/retry` | yes | [apps/api/app/api/internal_odoo.py](../../apps/api/app/api/internal_odoo.py) (`retry`) |
| GET | `/internal/v1/integrations/odoo/failures` | yes | [apps/api/app/api/internal_odoo.py](../../apps/api/app/api/internal_odoo.py) (`failures`) |
| GET | `/internal/v1/integrations/odoo/health` | yes | [apps/api/app/api/internal_odoo.py](../../apps/api/app/api/internal_odoo.py) (`health`) |
| GET | `/metrics` | yes | [apps/api/app/observability.py](../../apps/api/app/observability.py) (`metrics_response`) |
