import type { PortalConfig } from "@breero/portal";

/**
 * ops.breero.com — dispatch and operations.
 *
 * Every `source` here is a route that exists in apps/api/openapi.json today. Sections
 * without one state why, because manual dispatch currently runs through curl and an
 * operator needs to know which parts of that this console has replaced.
 */
export const opsPortalConfig: PortalConfig = {
  name: "Operations Portal",
  eyebrow: "Dispatch and operations",
  allowedRoles: ["operations", "ops_manager", "admin", "superadmin"],
  sections: [
    {
      slug: "dispatch-queue",
      label: "Dispatch queue",
      description:
        "Durable service requests awaiting manual dispatch. A request enters this queue when no provider had capacity, and it never promises the customer an appointment.",
      source: "/operations/dispatcher/queue",
      emptyTitle: "The queue is clear",
      emptyDescription: "No service requests are currently waiting for manual dispatch.",
      columns: [
        { key: "id", label: "Request" },
        { key: "status", label: "Status" },
        { key: "service_name", label: "Service" },
        { key: "postal_code", label: "ZIP" },
        { key: "created_at", label: "Received" },
      ],
      actions: [
        {
          label: "Start work",
          method: "PATCH",
          path: (row) => `/operations/dispatcher/queue/${String(row.id)}`,
          body: () => ({ status: "IN_PROGRESS" }),
          available: (row) => row.status === "PENDING" || row.status === "NEW",
        },
        {
          label: "Resolve",
          method: "PATCH",
          path: (row) => `/operations/dispatcher/queue/${String(row.id)}`,
          body: () => ({ status: "RESOLVED" }),
          confirm: "Mark this request resolved? It leaves the dispatch queue.",
          available: (row) => row.status !== "RESOLVED",
        },
      ],
    },
    {
      slug: "jobs",
      label: "Jobs",
      description:
        "Every job across providers. Assignment is explicit: only assigning the provider that holds the reserved slot moves a booking to CONFIRMED.",
      source: "/jobs",
      emptyTitle: "No jobs yet",
      emptyDescription: "Jobs appear here once a booking is paid for and confirmed.",
      columns: [
        { key: "id", label: "Job" },
        { key: "status", label: "Status" },
        { key: "scheduled_start", label: "Scheduled" },
        { key: "vendor_id", label: "Provider" },
        { key: "service_id", label: "Service" },
      ],
      actions: [
        {
          label: "Suggest matches",
          method: "POST",
          path: (row) => `/operations/jobs/${String(row.id)}/match`,
          body: () => ({}),
        },
      ],
    },
    {
      slug: "vendors",
      label: "Providers",
      description:
        "Provider accounts and their operational status. Suspending a provider stops new assignments; it does not cancel work already scheduled.",
      source: "/vendors",
      columns: [
        { key: "id", label: "Provider" },
        { key: "legal_name", label: "Legal name" },
        { key: "status", label: "Status" },
        { key: "created_at", label: "Onboarded" },
      ],
      actions: [
        {
          label: "Suspend",
          method: "PATCH",
          path: (row) => `/operations/vendors/${String(row.id)}/status`,
          body: () => ({ status: "SUSPENDED" }),
          confirm: "Suspend this provider? They will stop receiving new job offers.",
          destructive: true,
          available: (row) => row.status === "ACTIVE",
        },
        {
          label: "Reactivate",
          method: "PATCH",
          path: (row) => `/operations/vendors/${String(row.id)}/status`,
          body: () => ({ status: "ACTIVE" }),
          available: (row) => row.status === "SUSPENDED",
        },
      ],
    },
    {
      slug: "integration-health",
      label: "Integration health",
      description:
        "Outbox delivery health. A rising backlog here usually means the scheduler is not running rather than that the downstream is down.",
      source: "/integrations/health",
      columns: [
        { key: "status", label: "Status" },
        { key: "pending", label: "Pending", numeric: true },
        { key: "failed", label: "Failed", numeric: true },
        { key: "delivered", label: "Delivered", numeric: true },
      ],
    },
    {
      slug: "integration-failures",
      label: "Integration failures",
      description:
        "Events that exhausted their retries. Retrying resets the attempt count; fix the cause first, or it will simply fail again.",
      source: "/integrations/failures",
      emptyTitle: "No failed deliveries",
      emptyDescription: "Every integration event has been delivered or is still in flight.",
      columns: [
        { key: "id", label: "Event" },
        { key: "event_type", label: "Type" },
        { key: "last_error_code", label: "Error" },
        { key: "attempt_count", label: "Attempts", numeric: true },
        { key: "last_error_at", label: "Last attempt" },
      ],
      actions: [
        {
          label: "Retry",
          method: "POST",
          path: (row) => `/integrations/events/${String(row.id)}/retry`,
          confirm: "Retry this event? Retry only after the underlying cause is fixed.",
        },
      ],
    },
    {
      slug: "coverage",
      label: "Provider coverage",
      description:
        "Which providers cover which ZIP codes for which services, and their booking capacity.",
      blockedReason:
        "Coverage is replaced atomically through PUT /operations/workers/{worker_id}/booking-coverage, which takes a complete replacement set. There is no read endpoint to show current coverage, so this console cannot display what it would be overwriting.",
      blockedOn:
        "A GET counterpart for worker booking-coverage. Editing coverage without first showing it would risk silently dropping ZIPs.",
    },
    {
      slug: "bookings",
      label: "Bookings",
      description: "Bookings across all customers, with operator confirmation.",
      blockedReason:
        "POST /operations/bookings/{booking_id}/confirm exists, but there is no operator-scoped endpoint that lists bookings. The only list route is /customer/bookings, which is scoped to the signed-in customer.",
      blockedOn: "An operations-scoped booking list endpoint.",
    },
  ],
};
