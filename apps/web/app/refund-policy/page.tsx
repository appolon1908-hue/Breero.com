import type { Metadata } from "next";
import Link from "next/link";
import { LegalPage } from "@/components/marketing/LegalPage";
import { legalBusiness } from "@/content/legal";

export const metadata: Metadata = {
  title: "Refund & Return Policy",
  description: "Refund, credit and return rules for Breero marketplace and coordination services.",
  alternates: { canonical: "/refund-policy" },
};

export default function Page() {
  return (
    <LegalPage title="Refund & Return Policy" updated="12 August 2026">
      <p>
        Because Breero provides digital marketplace access, lead-generation services, coordination
        services and other service-related offerings, traditional physical-product returns generally
        do not apply unless Breero separately sells a returnable physical product.
      </p>
      <h2>Refund eligibility</h2>
      <p>
        Eligibility for a refund depends on the product or service purchased, the circumstances
        involved, the applicable agreement and applicable law. Refunds are reviewed case by case and
        are not automatic merely because a customer or provider changes their mind.
      </p>
      <h2>Underlying provider work</h2>
      <p>
        Customer refunds relating to an independent provider&apos;s underlying work may depend on
        the agreement between the customer and that provider unless Breero itself sold or expressly
        guaranteed the applicable service.
      </p>
      <h2>Professional leads</h2>
      <p>
        Professional paid-lead disputes are governed by the{" "}
        <Link href="/professional-lead-policy">Professional Lead & Refund Policy</Link>, including
        the applicable dispute period and qualification criteria.
      </p>
      <h2>Possible resolutions</h2>
      <p>
        Where appropriate, Breero may offer an account credit, negotiated credit, replacement lead,
        partial refund, full refund or another mutually agreed resolution, subject to the applicable
        program terms and law.
      </p>
      <h2>How to request review</h2>
      <p>
        Email <a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a> with
        the relevant request, booking, transaction or lead reference and a concise description of
        the issue. Do not send payment-card credentials by email.
      </p>
      <h2>Legal rights</h2>
      <p>
        Nothing in this policy limits rights or remedies that cannot legally be limited under
        applicable law.
      </p>
    </LegalPage>
  );
}
