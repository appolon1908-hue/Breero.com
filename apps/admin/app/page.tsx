import { PortalApp, type PortalConfig } from "@breero/portal";
const config: PortalConfig = {
  name: "Admin & Finance",
  eyebrow: "Governance workspace",
  allowedRoles: ["finance", "admin"],
  sections: [
    {
      label: "Service catalog",
      path: "/services",
      description: "The live service catalog and pricing modes exposed by the canonical API.",
    },
    {
      label: "Providers",
      path: "/vendors",
      description: "Provider approval records available to authorized administrators.",
    },
    {
      label: "Earnings",
      path: "/finance/earnings",
      description:
        "Authoritative provider earnings. This view never calculates or invents financial values.",
    },
    {
      label: "Integration health",
      path: "/integrations/health",
      description: "Current backend integration configuration and delivery health.",
    },
    {
      label: "Integration failures",
      path: "/integrations/failures",
      description: "Durable failures available for authorized investigation and retry.",
    },
    {
      label: "Users & roles",
      description: "User administration is not yet exposed by a canonical admin API.",
    },
    {
      label: "Payments & refunds",
      description: "Finance-wide payment and refund listing is not yet exposed by a canonical API.",
    },
    {
      label: "Lead disputes",
      description:
        "Finance-wide dispute review and resolution is not yet exposed by a canonical API.",
    },
    {
      label: "Payout batches",
      description: "Payout commands exist, but a list/read projection is not yet exposed.",
    },
    {
      label: "Audit log",
      description: "An admin-safe audit-log read operation is not yet exposed.",
    },
  ],
};
export default function Page() {
  return <PortalApp config={config} />;
}
