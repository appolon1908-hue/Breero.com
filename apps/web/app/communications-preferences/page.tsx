import { CommunicationPreferencesForm } from "@/components/legal/ComplianceForms";
import { LegalPage } from "@/components/marketing/LegalPage";
export default function Page() {
  return (
    <LegalPage title="Communications Preferences" updated="17 August 2026" version="2026.08.17">
      <p>
        Transactional email, transactional SMS, marketing email, and marketing SMS are separate
        purposes. Service requests work without marketing consent. Marketing email and SMS are
        currently disabled.
      </p>
      <CommunicationPreferencesForm />
      <p>
        Email unsubscribe does not require login. SMS revocation keywords are listed in the SMS
        Terms. Suppression applies across BREERO and connected delivery systems.
      </p>
    </LegalPage>
  );
}
