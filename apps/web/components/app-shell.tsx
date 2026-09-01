import type { ReactNode } from "react";
import { ToastProvider } from "@breero/ui";
import { SiteFooter } from "./site-footer";
import { SiteHeader } from "./site-header";
import { AdSenseLoader } from "./consent/AdSenseLoader";
import { CookieConsent } from "./consent/CookieConsent";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <ToastProvider>
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <SiteHeader />
      <main id="main-content" tabIndex={-1}>
        {children}
      </main>
      <SiteFooter />
      <AdSenseLoader />
      <CookieConsent />
    </ToastProvider>
  );
}
