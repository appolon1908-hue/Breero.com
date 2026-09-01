import type { Metadata } from "next";
import { LegalPage } from "@/components/marketing/LegalPage";
import { legalAddress, legalBusiness, legalIdentity } from "@/content/legal";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How Breero.com processes marketplace, service-request and provider information.",
  alternates: { canonical: "/privacy" },
};

export default function Page() {
  return (
    <LegalPage title="Privacy Policy" updated="12 August 2026">
      <p>
        <strong>{legalIdentity}</strong> operates Breero.com. Business address: {legalAddress}.
      </p>
      <h2>Information Breero may process</h2>
      <p>
        Breero may process information needed to operate its marketplace and coordination services,
        including customer identity and contact information, service address or general location,
        requested service, project details, appointment availability, communications, provider
        matching information, lead records, estimates or transaction-related information where
        applicable, support records, marketing attribution information, platform activity and
        security information.
      </p>
      <h2>How information is used</h2>
      <p>
        Information may be used to receive and evaluate requests, match or coordinate with
        potentially suitable providers, facilitate communications and scheduling, manage leads,
        provide support, maintain security, prevent abuse, improve the service, comply with legal
        obligations and resolve disputes.
      </p>
      <h2>Marketplace sharing</h2>
      <p>
        Information necessary to respond to a service request may be disclosed to or made available
        to independent service providers that may be able to fulfill the request. We aim to limit
        sharing to information reasonably relevant to the service or marketplace function involved.
      </p>
      <h2>Service providers and processors</h2>
      <p>
        Breero may use hosting, communications, analytics, security, payment, customer-support and
        other technology providers to operate the platform. Where payment functionality is enabled,
        card information should be handled through the applicable secure payment-provider interface
        rather than ordinary email or text.
      </p>
      <h2>Retention and security</h2>
      <p>
        Breero retains information for periods reasonably necessary for service coordination,
        marketplace administration, customer or provider support, security, accounting, dispute
        handling, legal obligations and legitimate business needs. Reasonable administrative,
        technical and organizational safeguards are used, but no internet system can be guaranteed
        completely secure.
      </p>
      <h2>Your choices and rights</h2>
      <p>
        Depending on applicable law, you may have rights relating to access, correction, deletion,
        restriction, objection or other treatment of personal information. Promotional
        communications may be opted out of using the method provided in the message, while service
        or transactional communications may remain necessary for an active request.
      </p>
      <h2>Contact</h2>
      <p>
        Privacy questions or requests can be sent to{" "}
        <a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a>. Do not
        send passwords, tokens or payment credentials. Corporate information is available at{" "}
        <a href={legalBusiness.corporateSite}>Codestra.co</a>.
      </p>
    </LegalPage>
  );
}
