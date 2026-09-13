import { PortalApp, type PortalConfig } from "@breero/portal";

const config: PortalConfig = {
  name: "Operations Portal",
  eyebrow: "Service operations",
  canonicalOrigin: "https://ops.breero.com",
  publicOrigin: "https://breero.com",
  supportEmail: "support@breero.com",
  allowedRoles: ["operations", "admin"],
  sections: [
    { label: "Live job queue", path: "/jobs", description: "Authorized live jobs, assignments, and current states." },
    { label: "Providers", path: "/vendors", description: "Provider records available to operations for matching and approval workflows." },
    { label: "Integration failures", path: "/integrations/failures", description: "Durable delivery failures that may require an authorized retry." },
    { label: "Integration health", path: "/integrations/health", description: "Configured integration and outbox delivery health." },
    { label: "Dispatch board", description: "Matching and assignment commands exist per job; a queue-level dispatch projection is not yet exposed." },
    { label: "Service-area map", description: "A privacy-safe geospatial operations projection is not yet exposed by the canonical API." },
    { label: "SLA monitoring", description: "An aggregated SLA endpoint is not yet exposed. No synthetic metrics are shown." },
  ],
};

export default function Page() {
  return <PortalApp config={config} />;
}
