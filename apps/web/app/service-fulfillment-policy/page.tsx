import type { Metadata } from "next";
import { LegalPage } from "@/components/marketing/LegalPage";
import { legalBusiness } from "@/content/legal";

export const metadata: Metadata = {
  title: "Service Fulfillment Policy",
  description:
    "How Breero coordinates service requests, matching, scheduling and independent-provider fulfillment.",
  alternates: { canonical: "/service-fulfillment-policy" },
};

export default function Page() {
  return (
    <LegalPage title="Service Fulfillment Policy" updated="12 August 2026">
      <p>
        Breero facilitates service requests, matching, scheduling, communications, lead delivery and
        related marketplace functions. Unless expressly stated otherwise, the underlying service is
        fulfilled by an independent service provider.
      </p>
      <h2>Request and matching</h2>
      <p>
        Customers provide the service category, location, requested work, availability and other
        relevant information. Breero may use that information, provider eligibility, service area,
        workload and other relevant factors to identify potentially suitable providers.
      </p>
      <h2>Estimate, scope and pricing</h2>
      <p>
        Unless Breero expressly states otherwise for a particular offering, the independent provider
        evaluates the requested work and communicates its estimate, proposed scope, availability,
        pricing, materials, access requirements, permits, payment terms, warranties and other
        service-specific conditions.
      </p>
      <h2>Customer decision</h2>
      <p>
        The customer may accept or reject a provider proposal. The existence of a Breero lead,
        match, appointment, estimate request or introduction does not require the customer to
        purchase the underlying service.
      </p>
      <h2>Provider fulfillment</h2>
      <p>
        When the customer and provider agree to proceed, the independent provider is responsible for
        completing the work it agrees to perform according to the terms agreed with the customer,
        except where a particular Breero offering expressly provides otherwise.
      </p>
      <h2>Breero follow-up</h2>
      <p>
        Breero may facilitate appointment status, communications, reviews, quality monitoring,
        dispute intake and other marketplace functions. These activities do not automatically make
        Codestra LLC or Breero the contractor or service provider merely because the transaction
        originated through the platform.
      </p>
      <h2>Support</h2>
      <p>
        Service coordination or fulfillment questions can be sent to{" "}
        <a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a>.
      </p>
    </LegalPage>
  );
}
