import type { Metadata } from "next";
import { LegalPage } from "@/components/marketing/LegalPage";
import { legalBusiness } from "@/content/legal";
export const metadata: Metadata = {
  title: "Accessibility Statement",
  alternates: { canonical: "/accessibility" },
};
export default function Page() {
  return (
    <LegalPage title="Accessibility Statement" updated="13 August 2026">
      <h2>Our approach</h2>
      <p>
        BREERO targets WCAG 2.2 Level AA through keyboard access, visible focus, readable contrast,
        semantic structure, reduced-motion support, screen-reader labels, and clear error feedback.
      </p>
      <h2>Assessment limits</h2>
      <p>
        Automated checks alone do not establish full conformance. BREERO combines automated and
        manual testing and records known limitations.
      </p>
      <h2>Feedback</h2>
      <p>
        Report an accessibility barrier to{" "}
        <a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a> with the
        page and task affected.
      </p>
    </LegalPage>
  );
}
