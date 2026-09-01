import { PrivacyRequestForm } from "@/components/legal/ComplianceForms";
import { LegalPage } from "@/components/marketing/LegalPage";
export default function Page() {
  return (
    <LegalPage
      title="U.S. State Privacy Rights and Choices"
      updated="17 August 2026"
      version="2026.08.17"
    >
      <p>
        Depending on where you live, you may request access, correction, deletion, or a portable
        copy of personal information and may opt out of sale, sharing, or targeted advertising. You
        may also appeal a denied request.
      </p>
      <h2>Submit a request</h2>
      <PrivacyRequestForm />
      <h2>Verification and tracking</h2>
      <p>
        BREERO verifies requests proportionately, records statutory deadlines, and provides a
        reference for status tracking. We retain a minimal suppression record when necessary to keep
        an opt-out effective.
      </p>
      <h2>Global Privacy Control</h2>
      <p>
        Where legally applicable, a recognized Global Privacy Control signal is treated as an
        opt-out of applicable sale, sharing, targeted advertising, and nonessential tracking for
        that browser.
      </p>
    </LegalPage>
  );
}
