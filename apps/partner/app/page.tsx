"use client";

import { PortalApp } from "@breero/portal";
import { partnerPortalConfig } from "./portal-config";

export default function Page() {
  return <PortalApp config={partnerPortalConfig} />;
}
