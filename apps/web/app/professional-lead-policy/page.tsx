import type { Metadata } from "next";
import { LegalPage } from "@/components/marketing/LegalPage";
import { legalBusiness } from "@/content/legal";

export const metadata: Metadata = {
  title: "Professional Lead & Refund Policy",
  description:
    "Paid lead pricing, qualification, dispute and refund rules for Breero professionals.",
  alternates: { canonical: "/professional-lead-policy" },
};

export default function Page() {
  return (
    <LegalPage title="Professional Lead & Refund Policy" updated="12 August 2026">
      <p>
        When a professional purchases a Breero lead, the professional is purchasing access to a
        customer opportunity subject to the description and qualification criteria applicable to
        that lead or lead program.
      </p>
      <h2>No guaranteed job or revenue</h2>
      <p>
        A lead is not a guaranteed completed job, sale, contract, appointment outcome or amount of
        revenue. The provider remains responsible for converting the opportunity into business.
        Conversion can depend on response time, availability, pricing, reputation, communication,
        estimates, sales process, service area, qualifications, reviews, scheduling and follow-up.
      </p>
      <h2>Lead price disclosure</h2>
      <p>
        Each paid lead should have its applicable price disclosed before or as part of the
        professional&apos;s purchase or acceptance process.
      </p>
      <h2>72-hour dispute period</h2>
      <p>
        A provider seeking review of a paid lead should submit the dispute within 72 hours of
        receiving the lead, subject to applicable law and any specific program terms presented at
        purchase. The provider should identify the lead, state the reason for dispute and provide
        reasonably available supporting information.
      </p>
      <h2>Potentially eligible issues</h2>
      <ul>
        <li>Materially incorrect or unusable customer contact information.</li>
        <li>A duplicate paid lead improperly charged to the same provider.</li>
        <li>A request clearly outside the purchased service category.</li>
        <li>A material mismatch with expressly disclosed lead qualification criteria.</li>
        <li>Another objectively documented defect materially affecting lead validity.</li>
      </ul>
      <h2>Events that do not automatically invalidate a lead</h2>
      <ul>
        <li>The customer rejects the estimate or considers the price too high.</li>
        <li>The customer changes their mind, postpones the project or chooses another provider.</li>
        <li>
          The customer obtains multiple estimates or does not answer an initial contact attempt.
        </li>
        <li>The provider cannot meet the requested schedule or does not adequately follow up.</li>
        <li>The lead does not convert into a completed job.</li>
      </ul>
      <h2>Review and remedies</h2>
      <p>
        Submitting a dispute does not automatically establish entitlement to a refund or credit.
        Breero reviews available records case by case. Where appropriate, a resolution may include
        account credit, negotiated credit, partial refund, full refund, replacement lead or another
        mutually agreed remedy.
      </p>
      <h2>How to dispute a lead</h2>
      <p>
        Email <a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a> with
        the subject “Lead Review” and include the lead reference, amount charged, reason for dispute
        and supporting information.
      </p>
      <h2>Legal rights</h2>
      <p>
        Nothing in this policy limits rights or remedies that cannot legally be limited under
        applicable law.
      </p>
    </LegalPage>
  );
}
