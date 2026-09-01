import type { Metadata } from "next";
import Link from "next/link";
import { LegalPage } from "@/components/marketing/LegalPage";
import { legalAddress, legalBusiness, legalIdentity } from "@/content/legal";
export const metadata: Metadata = { title: "Terms of Use", alternates: { canonical: "/terms" } };
export default function Page() {
  return (
    <LegalPage title="Terms of Use" updated="13 August 2026">
      <p>
        <strong>{legalIdentity}</strong> operates Breero.com, a service-coordination and
        lead-generation platform. Business address: {legalAddress}.
      </p>
      <h2>Marketplace role</h2>
      <p>
        BREERO connects customers with independent service providers. Unless a specific offering
        expressly says otherwise, BREERO does not perform the underlying contractor, trade, repair,
        maintenance, cleaning, hauling, installation, or other requested work.
      </p>
      <h2>Requests are not appointments</h2>
      <p>
        A service request or preferred time is not a confirmed appointment. Provider availability is
        not guaranteed. A recommendation is not an endorsement or guarantee. Automatic provider
        assignment and automatic confirmation are disabled; an authorized operator must approve the
        final match after eligibility and capacity checks.
      </p>
      <h2>Independent providers</h2>
      <p>
        Providers are responsible for workmanship, licensing, permits, insurance, estimates,
        pricing, scope, materials, safety, and legal compliance. Final scope, price, and performance
        are agreed between customer and provider unless expressly stated otherwise.
      </p>
      <h2>Quotes and payments</h2>
      <p>
        All work is quote-required. BREERO does not currently require or collect online payment.
        Card fields, checkout, charges, refunds, subscriptions, payouts, and paid-lead processing
        are disabled. Do not send card information by email, chat, or text.
      </p>
      <h2>Urgent requests</h2>
      <p>
        Sunday availability is for urgent home-service requests only. BREERO does not provide
        medical, emergency, or life-safety services. Call 911 or the appropriate emergency authority
        for life-safety emergencies.
      </p>
      <h2>Policies</h2>
      <p>
        Review the{" "}
        <Link href="/refund-cancellation">Refund, Rescheduling, and Cancellation Policy</Link>,{" "}
        <Link href="/service-fulfillment">Service Fulfillment and Appointment Policy</Link>,{" "}
        <Link href="/provider-terms">Provider Terms</Link>, and{" "}
        <Link href="/lead-terms">Lead Terms</Link>.
      </p>
      <h2>Non-waivable rights</h2>
      <p>Nothing in these Terms excludes a right or obligation that cannot lawfully be excluded.</p>
      <h2>Support</h2>
      <p>
        Contact <a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a>.
      </p>
    </LegalPage>
  );
}
