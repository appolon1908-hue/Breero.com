"use client";

import { PortalApp } from "@breero/portal";
import { adminPortalConfig } from "./portal-config";

export default function Page() {
  return <PortalApp config={adminPortalConfig} />;
}
