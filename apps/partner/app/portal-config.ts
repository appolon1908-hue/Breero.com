import type { PortalConfig } from "@breero/portal";

/**
 * partners.breero.com — the provider and technician workspace.
 *
 * The previous configuration described company profile, workers, qualifications and
 * availability as "awaiting a canonical backend operation". That was out of date for
 * most of them: provider profile, services, skills and onboarding all have live
 * routes. Only earnings and provider-owned availability are genuinely still blocked.
 */
export const partnerPortalConfig: PortalConfig = {
  name: "Partner Portal",
  eyebrow: "Provider workspace",
  allowedRoles: ["vendor_admin", "technician"],
  sections: [
    {
      slug: "jobs",
      label: "Jobs",
      description:
        "Job offers and assignments for your provider account. Status changes go through explicit commands, never free-form editing.",
      source: "/jobs",
      emptyTitle: "No jobs assigned",
      emptyDescription: "Assigned work will appear here as soon as operations dispatches it.",
      columns: [
        { key: "id", label: "Job" },
        { key: "status", label: "Status" },
        { key: "scheduled_start", label: "Scheduled" },
        { key: "service_id", label: "Service" },
      ],
      actions: [
        {
          label: "On my way",
          method: "POST",
          path: (row) => `/jobs/${String(row.id)}/technician/en-route`,
          available: (row) => row.status === "ASSIGNED" || row.status === "SCHEDULED",
        },
        {
          label: "Start",
          method: "POST",
          path: (row) => `/jobs/${String(row.id)}/technician/start`,
          available: (row) => row.status === "EN_ROUTE" || row.status === "ON_SITE",
        },
        {
          label: "Complete",
          method: "POST",
          path: (row) => `/jobs/${String(row.id)}/technician/complete`,
          confirm: "Mark this job complete? Completion is reported to operations.",
          available: (row) => row.status === "IN_PROGRESS",
        },
      ],
    },
    {
      slug: "profile",
      label: "Company profile",
      description: "Your provider record as BREERO holds it.",
      source: "/provider/profile",
      columns: [
        { key: "legal_name", label: "Legal name" },
        { key: "trading_name", label: "Trading name" },
        { key: "status", label: "Status" },
        { key: "contact_email", label: "Contact" },
      ],
    },
    {
      slug: "services",
      label: "Services offered",
      description:
        "The catalog services your account is approved to deliver. A selection can be withdrawn without deleting the record.",
      source: "/provider/services",
      emptyTitle: "No services selected",
      emptyDescription: "Select the catalog services you deliver to start receiving offers.",
      columns: [
        { key: "id", label: "Selection" },
        { key: "service_id", label: "Service" },
        { key: "status", label: "Status" },
        { key: "created_at", label: "Selected" },
      ],
      actions: [
        {
          label: "Withdraw",
          method: "DELETE",
          path: (row) => `/provider/services/${String(row.id)}`,
          confirm: "Withdraw this service? You will stop receiving offers for it.",
          destructive: true,
        },
      ],
    },
    {
      slug: "skills",
      label: "Skills",
      description: "Declared skills used when operations matches a job to a provider.",
      source: "/provider/skills",
      emptyTitle: "No skills declared",
      emptyDescription: "Declared skills help operations match the right work to you.",
      columns: [
        { key: "id", label: "Skill" },
        { key: "skill_key", label: "Skill key" },
        { key: "created_at", label: "Declared" },
      ],
      actions: [
        {
          label: "Remove",
          method: "DELETE",
          path: (row) => `/provider/skills/${String(row.id)}`,
          destructive: true,
        },
      ],
    },
    {
      slug: "onboarding",
      label: "Onboarding",
      description:
        "Your onboarding submission and its review state. Submitting locks the record for administrative review.",
      source: "/provider/onboarding",
      columns: [
        { key: "status", label: "Status" },
        { key: "submitted_at", label: "Submitted" },
        { key: "reviewed_at", label: "Reviewed" },
      ],
    },
    {
      slug: "leads",
      label: "Professional leads",
      description:
        "Opportunities eligible for your provider account. Purchasing access does not guarantee a completed job, sale, contract, appointment outcome, or revenue.",
      blockedReason:
        "Lead purchasing requires Stripe. PAID_LEADS_ENABLED and STRIPE_ENABLED are both off for this release, and the API returns 503 for purchase attempts, so there is nothing to list.",
      blockedOn: "The payments release.",
    },
    {
      slug: "availability",
      label: "Availability",
      description: "The hours and capacity you are bookable for.",
      blockedReason:
        "Booking coverage is operator-owned: the only route is PUT /operations/workers/{worker_id}/booking-coverage, which requires operator permission by design so capacity cannot be self-declared.",
      blockedOn:
        "A provider-scoped availability endpoint, if provider self-service is ever intended. PROVIDER_SELF_SERVICE_ENABLED is off.",
    },
    {
      slug: "earnings",
      label: "Earnings and payouts",
      description: "What you have earned, and when it will be paid.",
      blockedReason:
        "The finance domain computes earnings and payout batches, but no provider-scoped, privacy-filtered endpoint exposes them, and payment routes are absent from the API contract for this release.",
      blockedOn: "The payments release, plus a provider-scoped earnings endpoint.",
    },
  ],
};
