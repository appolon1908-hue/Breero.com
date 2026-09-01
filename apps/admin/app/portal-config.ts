import type { PortalConfig } from "@breero/portal";

/**
 * admin.breero.com — administration and finance.
 *
 * Finance is the notable gap. The payment and payout domains are fully built but
 * gated off for this release, so their routes are not in the OpenAPI document at
 * all — `scripts/check-frontend-openapi.mjs` actively fails if they appear. Those
 * sections say so rather than rendering an empty ledger.
 */
export const adminPortalConfig: PortalConfig = {
  name: "Administration Portal",
  eyebrow: "Administration and finance",
  allowedRoles: ["admin", "superadmin", "finance"],
  sections: [
    {
      slug: "provider-applications",
      label: "Provider applications",
      description:
        "Provider onboarding submissions awaiting review. Approval provisions a live provider account, so it is confirmed before it is sent.",
      source: "/admin/provider-applications",
      emptyTitle: "No applications waiting",
      emptyDescription: "Every submitted provider application has been decided.",
      columns: [
        { key: "id", label: "Application" },
        { key: "legal_name", label: "Legal name" },
        { key: "status", label: "Status" },
        { key: "submitted_at", label: "Submitted" },
      ],
      actions: [
        {
          label: "Approve",
          method: "POST",
          path: (row) => `/admin/provider-applications/${String(row.id)}/approve`,
          confirm: "Approve this application? It provisions a live provider account.",
          available: (row) => row.status !== "APPROVED",
        },
        {
          label: "Request info",
          method: "POST",
          path: (row) => `/admin/provider-applications/${String(row.id)}/request-information`,
          body: () => ({ message: "Further information is required to continue this review." }),
          available: (row) => row.status !== "APPROVED",
        },
        {
          label: "Reject",
          method: "POST",
          path: (row) => `/admin/provider-applications/${String(row.id)}/reject`,
          body: () => ({ reason: "Rejected during administrative review." }),
          confirm: "Reject this application? The applicant is notified of the decision.",
          destructive: true,
          available: (row) => row.status !== "APPROVED" && row.status !== "REJECTED",
        },
      ],
    },
    {
      slug: "service-zones",
      label: "Service zones",
      description:
        "Geographic zones that decide where each service can be booked. Deletion is an auditable deactivation, so historic booking and routing evidence survives.",
      source: "/admin/service-zones",
      columns: [
        { key: "id", label: "Zone" },
        { key: "name", label: "Name" },
        { key: "is_active", label: "Active" },
        { key: "priority", label: "Priority", numeric: true },
      ],
    },
    {
      slug: "postal-codes",
      label: "Postal codes",
      description:
        "ZIP routing. A configured but inactive postal row never falls back to city or state coverage — it simply does not match.",
      source: "/admin/postal-codes",
      columns: [
        { key: "id", label: "Row" },
        { key: "postal_code", label: "ZIP" },
        { key: "city", label: "City" },
        { key: "state_code", label: "State" },
        { key: "is_active", label: "Active" },
      ],
    },
    {
      slug: "services",
      label: "Service catalog",
      description: "The twelve catalog services and their pricing and bookability.",
      source: "/services",
      columns: [
        { key: "id", label: "Service" },
        { key: "name", label: "Name" },
        { key: "slug", label: "Slug" },
        { key: "base_price", label: "Base price", numeric: true },
        { key: "is_active", label: "Active" },
      ],
    },
    {
      slug: "access-catalog",
      label: "Roles and permissions",
      description:
        "The effective permission catalog. Permissions are resolved server-side on every request; this is the reference, not the enforcement.",
      source: "/auth/access/catalog",
      columns: [
        { key: "role_key", label: "Role" },
        { key: "permission", label: "Permission" },
        { key: "department", label: "Department" },
      ],
    },
    {
      slug: "email-outbox",
      label: "Email outbox",
      description:
        "Tenant email delivery. Retrying resets the attempt count, so fix the cause before retrying or it will fail the same way.",
      source: "/email/outbox",
      emptyTitle: "Nothing queued",
      emptyDescription: "No tenant email is waiting for delivery or has failed.",
      columns: [
        { key: "id", label: "Event" },
        { key: "message_id", label: "Message" },
        { key: "status", label: "Status" },
        { key: "attempts", label: "Attempts", numeric: true },
        { key: "last_error_code", label: "Error" },
      ],
      actions: [
        {
          label: "Retry",
          method: "POST",
          path: (row) => `/email/outbox/${String(row.id)}/retry`,
          confirm: "Retry this message? Retry only after the delivery cause is fixed.",
        },
      ],
    },
    {
      slug: "email-domains",
      label: "Email domains",
      description: "Sending domains and their verification state. Unverified domains cannot send.",
      source: "/email/domains",
      columns: [
        { key: "id", label: "Domain" },
        { key: "domain", label: "Name" },
        { key: "verification_status", label: "Verification" },
        { key: "active", label: "Active" },
      ],
      actions: [
        {
          label: "Mark verified",
          method: "POST",
          path: (row) => `/email/domains/${String(row.id)}/verification?verified=true`,
          confirm: "Mark this domain verified? Verified domains are permitted to send.",
          available: (row) => row.verification_status !== "VERIFIED",
        },
      ],
    },
    {
      slug: "finance",
      label: "Finance and payouts",
      description: "Provider earnings, payout batches, and the settlement ledger.",
      blockedReason:
        "The finance and payout domains are built, but every payment route is deliberately absent from the OpenAPI document for this release — the frontend contract check fails the build if one appears. There is nothing to read against without re-enabling payments.",
      blockedOn:
        "The payments release: PAYMENTS_ENABLED and PAYOUT_ENABLED, which Settings.validate_production currently refuses to boot with.",
    },
    {
      slug: "audit",
      label: "Audit log",
      description: "Who changed what, when, and under which request.",
      blockedReason:
        "Audit rows are written for every state change and now carry request, correlation and caller IP, but no endpoint exposes them for search.",
      blockedOn: "A read endpoint over audit_logs with filtering by actor, resource and date.",
    },
    {
      slug: "privacy-requests",
      label: "Privacy requests",
      description: "Data access and erasure requests and their fulfilment state.",
      blockedReason:
        "GET /privacy-requests/{request_id} can fetch one request by id, but there is no list endpoint, so this console cannot show which requests are outstanding.",
      blockedOn: "A list endpoint for privacy requests.",
    },
  ],
};
