import type { Metadata } from "next";
import Link from "next/link";
import { LegalPage } from "@/components/marketing/LegalPage";
export const metadata: Metadata = {
  title: "Cookies",
  description: "BREERO cookie information.",
  alternates: { canonical: "/cookies" },
};
export default function Page() {
  return (
    <LegalPage title="Cookie information" updated="17 August 2026" version="2026.08.17">
      <h2>Essential storage</h2>
      <p>
        BREERO uses necessary browser storage for consent choices, account security, session
        continuity and requested booking functions. Necessary storage cannot be disabled through the
        preference tool.
      </p>
      <h2>Optional analytics</h2>
      <p>
        With permission, BREERO may use first-party identifiers and campaign attribution to
        understand page and booking usage. Existing analytics-only choices are treated as
        advertising denied.
      </p>
      <h2>Optional advertising</h2>
      <p>
        Advertising technology is disabled by default. If Google AdSense is configured, Google and
        its partners may use cookies or identifiers for ad delivery, measurement, fraud prevention
        and, where separately permitted, personalization. Advertising code loads only after explicit
        advertising consent.
      </p>
      <h2>Your choices</h2>
      <p>
        You can <Link href="/cookie-preferences">manage or withdraw optional consent</Link> at any
        time. Withdrawal removes BREERO&apos;s optional analytics attribution and anonymous-session
        identifiers. You can also clear browser storage through browser settings.
      </p>
    </LegalPage>
  );
}
