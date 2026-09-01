import { LegalPage } from "@/components/marketing/LegalPage";
import { legalBusiness } from "@/content/legal";
export default function Page() {
  return (
    <LegalPage title="Cancellation Policy" updated="13 August 2026">
      <p>
        BREERO does not currently collect online payments or impose an online cancellation fee.
        Customers should cancel or request rescheduling as early as possible.
      </p>
      <h2>Requests and appointments</h2>
      <p>
        A requested time is not confirmed. A rescheduled time requires renewed capacity checks and
        authorized operator confirmation. Provider-specific terms must be disclosed and agreed
        separately.
      </p>
      <h2>How to cancel or reschedule</h2>
      <p>
        Email <a href={`mailto:${legalBusiness.supportEmail}`}>{legalBusiness.supportEmail}</a> with
        the appointment reference.
      </p>
    </LegalPage>
  );
}
