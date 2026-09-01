"use client";

import { PortalApp } from "@breero/portal";
import { opsPortalConfig } from "./portal-config";

export default function Page() {
  return <PortalApp config={opsPortalConfig} />;
}
