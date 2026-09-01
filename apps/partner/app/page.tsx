import { PortalApp, type PortalConfig } from "@breero/portal";
const config: PortalConfig = {
  name: "Partner Portal",
  eyebrow: "Provider workspace",
  allowedRoles: ["vendor_admin"],
  sections: [
    {
      label: "Professional leads",
      path: "/provider/leads",
      description:
        "Live opportunities eligible for your provider account. Purchasing access does not guarantee a completed job, sale, contract, appointment outcome, or revenue.",
    },
    {
      label: "Jobs",
      path: "/jobs",
      description: "Authorized job offers and assignments from the live BREERO API.",
    },
    {
      label: "Company profile",
      description:
        "Provider profile updates require a canonical provider-profile operation that is not yet exposed.",
    },
    {
      label: "Workers",
      description:
        "Worker records require the provider identity returned by the account context; no cross-provider lookup is attempted.",
    },
    {
      label: "Qualifications",
      description:
        "Document and qualification management is awaiting its canonical backend operation.",
    },
    {
      label: "Availability",
      description:
        "Provider-owned availability management is awaiting its canonical backend operation.",
    },
    {
      label: "Earnings & payouts",
      description:
        "Provider-owned earnings and payout history are awaiting privacy-scoped backend operations.",
    },
  ],
};
export default function Page() {
  return <PortalApp config={config} />;
}
